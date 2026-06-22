from __future__ import annotations

from collections.abc import Iterable
import copy
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import yaml
from modwire.extractors.loader import (
    load_extractor,
    supported_languages as supported_source_kinds,
)

import enclosure.features.architecture.config
import enclosure.features.workspace.config
import enclosure.features.workspace.rules
from enclosure.shared import layout

from . import domain

_PROJECT_OWNED_CONFIG_MAPS = {
    ("workspace", "recipe", "roles_map"),
}


class _FlowMapping(dict[object, object]):
    pass


class _MigratedConfigDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: object) -> bool:
        return True

    def increase_indent(
        self,
        flow: bool = False,
        indentless: bool = False,
    ) -> None:
        super().increase_indent(flow, indentless=False)


@dataclass(frozen=True)
class _MigratedConfig:
    content: str
    changed: bool
    warnings: tuple[str, ...]


class FileRepository:
    def load(self, path: Path, *, source_kind: str = "") -> domain.Workspace:
        project_root = Path(path).resolve()
        workspace_layout = layout.EnclosureProjectLayout()
        shared_rule_documents = self._load_shared_rule_documents()
        packaged_config_content = _packaged_text("enclosure.yaml")
        selected_extractor = source_kind or _existing_config_extractor(
            workspace_layout.config_path(project_root, None)
        )
        config_content = _bootstrap_config_content(
            project_root,
            packaged_config_content,
            source_kind=selected_extractor,
        )
        migrated_config = self._migrated_config(
            project_root,
            workspace_layout,
            config_content,
            fallback_config_content=config_content,
        )
        bootstrap_instruction_content = _packaged_text("copilot-instructions.md")
        agent_instruction_content = _packaged_text("AGENTS.md")

        validate_generated_assets(
            config_content=config_content,
            bootstrap_instruction_content=bootstrap_instruction_content,
            agent_instruction_content=agent_instruction_content,
            shared_rule_documents=shared_rule_documents,
        )

        return domain.Workspace(
            project_root=project_root,
            shared_rule_documents=shared_rule_documents,
            config_content=config_content,
            migrated_config_content=migrated_config.content,
            config_changed=migrated_config.changed,
            config_warnings=migrated_config.warnings,
            bootstrap_instruction_content=bootstrap_instruction_content,
            agent_instruction_content=agent_instruction_content,
            existing_shared_rule_paths=self._existing_shared_rule_paths(
                project_root,
                workspace_layout,
                shared_rule_documents,
            ),
            local_paths=self._list_workspace_files(
                workspace_layout.local_rules_dir(project_root)
            ),
            enclosure_dir_exists=workspace_layout.target_dir(project_root).is_dir(),
            config_exists=workspace_layout.config_path(project_root, None).is_file(),
            bootstrap_instruction_exists=workspace_layout.bootstrap_instruction_path(
                project_root
            ).is_file(),
            agent_instruction_exists=workspace_layout.agent_instruction_path(
                project_root
            ).is_file(),
            layout=workspace_layout,
        )

    def _load_shared_rule_documents(self) -> tuple[domain.SharedRuleDocument, ...]:
        rules_root = files("enclosure").joinpath("resources", "rules")
        return tuple(
            domain.SharedRuleDocument(
                shared_rule_path=domain.SharedRulePath(child_relative_path),
                content=child.read_text(encoding="utf-8"),
            )
            for child_relative_path, child in _iter_visible_files(
                rules_root,
                relative_path=Path(),
                suffix=".md",
            )
        )

    def _existing_shared_rule_paths(
        self,
        project_root: Path,
        workspace_layout: layout.EnclosureProjectLayout,
        shared_rule_documents: tuple[domain.SharedRuleDocument, ...],
    ) -> tuple[Path, ...]:
        rules_dir = workspace_layout.rules_dir(project_root)
        return tuple(
            target_path
            for target_path in (
                rules_dir / document.shared_rule_path.value
                for document in shared_rule_documents
            )
            if target_path.is_file()
        )

    def _list_workspace_files(self, root: Path) -> tuple[Path, ...]:
        if not root.is_dir():
            return ()

        return tuple(
            path
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
            if path.is_file()
            and not any(part.startswith(".") for part in path.relative_to(root).parts)
        )

    def _migrated_config(
        self,
        project_root: Path,
        workspace_layout: layout.EnclosureProjectLayout,
        packaged_config_content: str,
        *,
        fallback_config_content: str,
    ) -> "_MigratedConfig":
        config_path = workspace_layout.config_path(project_root, None)
        if not config_path.is_file():
            return _MigratedConfig(
                content=fallback_config_content,
                changed=False,
                warnings=(),
            )

        try:
            existing_text = config_path.read_text(encoding="utf-8")
        except OSError as exc:
            return _MigratedConfig(
                content=packaged_config_content,
                changed=False,
                warnings=(f"Could not read existing config: {exc}",),
            )

        try:
            existing_data = yaml.safe_load(existing_text)
        except yaml.YAMLError as exc:
            return _MigratedConfig(
                content=existing_text,
                changed=False,
                warnings=(f"Invalid enclosure.yaml syntax: {exc}",),
            )
        try:
            packaged_data = yaml.safe_load(packaged_config_content)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid generated config asset: {exc}") from exc

        if not isinstance(existing_data, dict):
            return _MigratedConfig(
                content=existing_text,
                changed=False,
                warnings=("Existing enclosure.yaml must contain a mapping at the top level",),
            )
        if not isinstance(packaged_data, dict):
            raise ValueError("Invalid generated config asset: top level must be a mapping")

        merged_data = copy.deepcopy(existing_data)
        warnings: list[str] = []
        changed = _merge_missing_config_values(
            merged_data,
            packaged_data,
            warnings,
            path=(),
        )
        if not changed:
            return _MigratedConfig(
                content=existing_text,
                changed=False,
                warnings=tuple(warnings),
            )

        return _MigratedConfig(
            content=_dump_migrated_config(merged_data),
            changed=True,
            warnings=tuple(warnings),
        )


file_repository = FileRepository()


def validate_generated_assets(
    *,
    config_content: str,
    bootstrap_instruction_content: str,
    agent_instruction_content: str,
    shared_rule_documents: tuple[domain.SharedRuleDocument, ...],
) -> None:
    _validate_generated_config(config_content)
    _validate_generated_instruction(
        "copilot-instructions.md",
        bootstrap_instruction_content,
    )
    _validate_generated_instruction("AGENTS.md", agent_instruction_content)
    _validate_generated_rule_documents(shared_rule_documents)


def _validate_generated_config(content: str) -> None:
    raw_data = _load_generated_yaml_mapping(
        content,
        label="Generated config asset",
        path=Path("resources/enclosure.yaml"),
    )
    try:
        enclosure.features.architecture.config.ArchitectureConfig.validate_mapping(
            raw_data,
            Path("resources/enclosure.yaml"),
        )
        enclosure.features.workspace.config.WorkspaceConfig.validate_mapping(
            raw_data,
            Path("resources/enclosure.yaml"),
        )
    except (
        enclosure.features.architecture.config.ArchitectureConfigError,
        enclosure.features.workspace.config.WorkspaceConfigError,
    ) as exc:
        raise ValueError(f"Invalid generated config asset: {exc}") from exc


def _validate_generated_instruction(name: str, content: str) -> None:
    if not content.strip():
        raise ValueError(f"Generated instruction asset must not be empty: {name}")


def _validate_generated_rule_documents(
    documents: tuple[domain.SharedRuleDocument, ...],
) -> None:
    policy = enclosure.features.workspace.rules.RuleSchemaPolicy.default()
    document_files = tuple(
        enclosure.features.workspace.rules.RuleDocumentFile(
            path=document.shared_rule_path.value,
            content=document.content,
        )
        for document in documents
    )
    known_paths = {document_file.path for document_file in document_files}

    for document_file in document_files:
        try:
            document_check = policy.inspect_document(document_file)
        except enclosure.features.workspace.rules.RuleDocumentParseError as exc:
            raise ValueError(
                "Invalid generated rule asset "
                f"{document_file.path.as_posix()}: {exc}"
            ) from exc

        violations = document_check.violations + policy.validate_references(
            document=document_check.document,
            known_paths=known_paths,
        )
        if violations:
            violation = violations[0]
            raise ValueError(
                "Invalid generated rule asset "
                f"{document_file.path.as_posix()}: "
                f"{violation.code}: {violation.message}"
            )


def _load_generated_yaml_mapping(
    content: str,
    *,
    label: str,
    path: Path,
) -> dict[str, object]:
    try:
        raw_data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid {label.lower()} syntax in {path}") from exc

    if raw_data is None:
        raw_data = {}

    if not isinstance(raw_data, dict):
        raise ValueError(f"{label} must contain a mapping at the top level: {path}")
    return raw_data


def _existing_config_extractor(config_path: Path) -> str:
    if not config_path.is_file():
        return ""
    try:
        raw_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return ""
    if not isinstance(raw_data, dict):
        return ""
    contract_section = raw_data.get("architecture")
    if not isinstance(contract_section, dict):
        return ""
    extractor = contract_section.get("language")
    return extractor if isinstance(extractor, str) else ""


def _bootstrap_config_content(
    project_root: Path,
    packaged_config_content: str,
    *,
    source_kind: str,
) -> str:
    raw_data = _load_generated_yaml_mapping(
        packaged_config_content,
        label="Generated config asset",
        path=Path("resources/enclosure.yaml"),
    )
    selected_extractor = _selected_extractor(project_root, source_kind)
    contract_section = _mapping_section(raw_data, "architecture")
    workspace = _mapping_section(raw_data, "workspace")
    recipe = _mapping_section(workspace, "recipe")

    contract_section["language"] = selected_extractor
    contract_section["root"] = "src" if (project_root / "src").is_dir() else "."
    contract_section["exclusions"] = [".enclosure/**"]
    recipe["skip"] = []
    recipe["roles_map"] = {}
    return _dump_migrated_config(raw_data)


def _selected_extractor(project_root: Path, requested_source_kind: str) -> str:
    normalized_source_kind = requested_source_kind.strip().lower()
    if normalized_source_kind:
        if normalized_source_kind not in supported_source_kinds():
            supported = ", ".join(supported_source_kinds())
            raise ValueError(
                f"Unsupported source extractor: {requested_source_kind}. "
                f"Supported: {supported}"
            )
        return normalized_source_kind

    counts = _supported_extractor_source_counts(project_root)
    if len(counts) == 1:
        return next(iter(counts))
    if not counts:
        supported = ", ".join(supported_source_kinds())
        raise ValueError(
            "Could not detect a source extractor. "
            f"Run `enclosure workspace sync init --language <language>`. "
            f"Supported: {supported}"
        )
    choices = ", ".join(
        f"{extractor}={count}" for extractor, count in sorted(counts.items())
    )
    raise ValueError(
        "Ambiguous source extractor. "
        f"Detected supported source files: {choices}. "
        "Run `enclosure workspace sync init --language <language>`."
    )


def _supported_extractor_source_counts(project_root: Path) -> dict[str, int]:
    suffixes_by_extractor = {
        extractor: tuple(load_extractor(extractor).file_extensions)
        for extractor in supported_source_kinds()
    }
    counts = {extractor: 0 for extractor in suffixes_by_extractor}
    for path in _iter_project_files(project_root):
        for extractor, suffixes in suffixes_by_extractor.items():
            if path.suffix in suffixes:
                counts[extractor] += 1
    return {
        extractor: count
        for extractor, count in counts.items()
        if count > 0
    }


def _iter_project_files(project_root: Path) -> Iterable[Path]:
    excluded_roots = {".enclosure", ".git", ".dev", ".venv", "build", "dist"}
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(project_root).parts
        if relative_parts and relative_parts[0] in excluded_roots:
            continue
        yield path


def _mapping_section(data: dict[object, object], key: str) -> dict[object, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Generated config asset section must be a mapping: {key}")
    return value


def _merge_missing_config_values(
    target: dict[object, object],
    defaults: dict[object, object],
    warnings: list[str],
    *,
    path: tuple[str, ...],
) -> bool:
    if path in _PROJECT_OWNED_CONFIG_MAPS:
        return False

    changed = False
    for key in target:
        if key not in defaults:
            warnings.append(f"Unknown config key preserved: {_config_path_label((*path, key))}")

    for key, default_value in defaults.items():
        current_path = (*path, str(key))
        if key not in target:
            target[key] = copy.deepcopy(default_value)
            changed = True
            continue

        target_value = target[key]
        if isinstance(default_value, dict):
            if isinstance(target_value, dict):
                changed = (
                    _merge_missing_config_values(
                        target_value,
                        default_value,
                        warnings,
                        path=current_path,
                    )
                    or changed
                )
                continue
            warnings.append(
                "Cannot merge config section because existing value is not a mapping: "
                f"{_config_path_label(current_path)}"
            )
    return changed


def _config_path_label(path: tuple[object, ...]) -> str:
    return ".".join(str(part) for part in path)


def _dump_migrated_config(data: dict[object, object]) -> str:
    return yaml.dump(
        _with_compact_yaml_objects(data),
        Dumper=_MigratedConfigDumper,
        default_flow_style=False,
        sort_keys=False,
    )


def _with_compact_yaml_objects(
    value: object,
    *,
    in_sequence: bool = False,
) -> object:
    if isinstance(value, list):
        return [_with_compact_yaml_objects(item, in_sequence=True) for item in value]

    if isinstance(value, dict):
        converted_items = {
            key: _with_compact_yaml_objects(item) for key, item in value.items()
        }
        if not value or (
            not in_sequence and all(_is_yaml_scalar(item) for item in value.values())
        ):
            return _FlowMapping(converted_items)
        return converted_items

    return value


def _is_yaml_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _represent_flow_mapping(
    dumper: yaml.SafeDumper,
    data: _FlowMapping,
) -> yaml.nodes.MappingNode:
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)


_MigratedConfigDumper.add_representer(_FlowMapping, _represent_flow_mapping)


class WorkspaceWritePlanMaterializer:
    def materialize(self, write_plan: domain.WorkspaceWritePlan):
        created_dir = self._ensure_target_dir(write_plan.target_dir)
        self._ensure_required_dirs(write_plan.required_dirs)
        created_files: list[Path] = []
        updated_files: list[Path] = []
        preserved_files = list(write_plan.preserved_paths)

        for change in write_plan.changes:
            if (
                change.action is domain.SyncAction.UPDATE
                and self._has_same_content(change)
            ):
                preserved_files.append(change.target_path)
                continue

            self._write_sync_change(change)
            if change.action is domain.SyncAction.CREATE:
                created_files.append(change.target_path)
            else:
                updated_files.append(change.target_path)

        return {
            "target_dir": write_plan.target_dir,
            "created_dir": created_dir,
            "created_files": tuple(created_files),
            "updated_files": tuple(updated_files),
            "preserved_files": tuple(preserved_files),
        }

    def _ensure_target_dir(self, target_dir: Path) -> bool:
        if target_dir.exists() and not target_dir.is_dir():
            raise NotADirectoryError(f"{target_dir} exists but is not a directory")

        if target_dir.is_dir():
            return False

        target_dir.mkdir(parents=True, exist_ok=True)
        return True

    def _ensure_required_dirs(self, required_dirs: tuple[Path, ...]) -> None:
        for required_dir in required_dirs:
            required_dir.mkdir(parents=True, exist_ok=True)

    def _has_same_content(self, change: domain.SyncChange) -> bool:
        return (
            change.target_path.is_file()
            and change.target_path.read_text(encoding="utf-8") == change.content
        )

    def _write_sync_change(self, change: domain.SyncChange) -> None:
        change.target_path.parent.mkdir(parents=True, exist_ok=True)
        change.target_path.write_text(change.content, encoding="utf-8")


write_plan_materializer = WorkspaceWritePlanMaterializer()


def _iter_visible_files(
    directory,
    *,
    relative_path: Path,
    suffix: str | None,
) -> Iterable[tuple[Path, object]]:
    for child in sorted(directory.iterdir(), key=lambda item: item.name):
        if child.name.startswith("."):
            continue

        child_relative_path = relative_path / child.name
        if child.is_dir():
            yield from _iter_visible_files(
                child,
                relative_path=child_relative_path,
                suffix=suffix,
            )
            continue

        if suffix is not None and child_relative_path.suffix != suffix:
            continue

        yield child_relative_path, child


def _packaged_text(name: str) -> str:
    return files("enclosure").joinpath("resources", name).read_text(encoding="utf-8")
