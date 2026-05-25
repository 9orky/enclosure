from __future__ import annotations

from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path

import yaml

import enclosure.features.architecture.config
import enclosure.features.workspace.config
import enclosure.features.workspace.rules
from enclosure.shared import layout

from . import domain


class FileRepository:
    def load(self, path: Path) -> domain.Workspace:
        project_root = Path(path).resolve()
        workspace_layout = layout.EnclosureProjectLayout()
        shared_rule_documents = self._load_shared_rule_documents()
        config_content = _packaged_text("enclosure.yaml")
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
