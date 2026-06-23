from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from enclosure.shared import templates
from enclosure.shared.config import settings

from . import domain


class _PatternManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    role: str = ""
    description: str = ""
    ladder: dict[str, Any] = Field(default_factory=dict)
    includes: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    roles_map: dict[str, str] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    files: list[dict[str, Any]] = Field(default_factory=list)


def current_pattern_root() -> Path:
    return settings.metadata.recipes_dir


def load_fit_config() -> domain.PatternFitConfig:
    return domain.PatternFitConfig.from_config(settings.query("workspace.recipe"))


class FilePatternRepository:
    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def find_all(self) -> tuple[domain.Pattern, ...]:
        if not self.root_path.is_dir():
            return ()

        return tuple(
            self._load_pattern(pattern_root, _pattern_manifest_path(pattern_root))
            for pattern_root in sorted(
                self._iter_pattern_roots(),
                key=lambda path: path.name,
            )
        )

    def get_by_name(self, name: str) -> domain.Pattern:
        pattern_root = self.root_path / name
        manifest_path = _pattern_manifest_path(pattern_root)
        if not manifest_path.is_file():
            raise LookupError(name)

        return self._load_pattern(pattern_root, manifest_path)

    def _iter_pattern_roots(self):
        for child in self.root_path.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir() and _pattern_manifest_path(child).is_file():
                yield child

    def _load_pattern(self, pattern_root: Path, manifest_path: Path) -> domain.Pattern:
        raw_data = _load_yaml_mapping(manifest_path)
        return _pattern_from_manifest(pattern_root, manifest_path, raw_data)


class FilePatternRenderer:
    def render_files(
        self,
        pattern: domain.Pattern,
        *,
        project_root: Path,
        context: dict[str, Any],
    ) -> tuple[domain.RenderedPatternFile, ...]:
        rendered_files: list[domain.RenderedPatternFile] = []
        for pattern_file in pattern.files:
            template_path = pattern_file.source
            if not template_path.is_absolute():
                template_path = pattern.root_path / template_path
            if not template_path.is_file():
                raise ValueError(f"Pattern template does not exist: {template_path}")

            rendered_target = templates.render_recipe_template(pattern_file.target, context)
            relative_path = _normalize_relative_path(rendered_target)
            rendered_files.append(
                domain.RenderedPatternFile(
                    source_path=template_path,
                    target_path=project_root / relative_path,
                    relative_path=relative_path,
                    content=templates.render_recipe_template(
                        template_path.read_text(encoding="utf-8"),
                        context,
                    ),
                )
            )
        return tuple(rendered_files)


class FilePatternMaterializer:
    def write_files(
        self,
        rendered_files: tuple[domain.RenderedPatternFile, ...],
        *,
        create_paths: tuple[Path, ...],
    ) -> None:
        create_path_set = set(create_paths)
        for rendered_file in rendered_files:
            if rendered_file.target_path not in create_path_set:
                continue
            rendered_file.target_path.parent.mkdir(parents=True, exist_ok=True)
            rendered_file.target_path.write_text(rendered_file.content, encoding="utf-8")


def normalize_target_path(project_root: Path, target_path: Path | str) -> Path:
    raw_path = Path(target_path)
    if not raw_path.is_absolute():
        return _normalize_relative_path(raw_path)
    try:
        return _normalize_relative_path(raw_path.resolve(strict=False).relative_to(project_root))
    except ValueError as exc:
        raise ValueError("Target path must stay inside the project root") from exc


def _normalize_relative_path(value: Path | str) -> Path:
    normalized_value = Path(str(value).strip().replace("\\", "/"))
    if normalized_value.is_absolute():
        raise ValueError("Pattern paths must be relative")
    if not normalized_value.parts:
        raise ValueError("Pattern paths must not be empty")
    if any(part in {".", ".."} for part in normalized_value.parts):
        raise ValueError("Pattern paths must not traverse outside the target root")
    return normalized_value


def _pattern_from_manifest(
    pattern_root: Path,
    manifest_path: Path,
    raw_data: dict[str, Any],
) -> domain.Pattern:
    try:
        manifest = _PatternManifest.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid Pattern manifest: {exc}") from exc

    if manifest.schema_version != 1:
        raise ValueError(f"Unsupported Pattern schema_version in {manifest_path}")

    return domain.Pattern(
        name=pattern_root.name,
        root_path=pattern_root,
        includes=_string_list(manifest.includes, "Pattern includes must be strings"),
        inputs=tuple(_input_specs_from(manifest.inputs)),
        files=tuple(_pattern_files_from(manifest.files)),
    )


def _pattern_manifest_path(pattern_root: Path) -> Path:
    return pattern_root / "recipe.yaml"


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ValueError(f"Could not read Pattern manifest: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid Pattern manifest syntax in {path}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError(f"Pattern manifest must contain a mapping at the top level: {path}")
    return raw_data


def _input_specs_from(raw_inputs: Any) -> tuple[domain.PatternInputSpec, ...]:
    if raw_inputs is None:
        return ()
    if not isinstance(raw_inputs, dict):
        raise ValueError("Pattern inputs must be a mapping")

    specs: list[domain.PatternInputSpec] = []
    for name, raw_spec in raw_inputs.items():
        if raw_spec is None:
            raw_spec = {}
        if not isinstance(name, str) or not isinstance(raw_spec, dict):
            raise ValueError("Pattern inputs must be named mappings")

        raw_default = raw_spec.get("default")
        raw_default_from = raw_spec.get("default_from")
        specs.append(
            domain.PatternInputSpec(
                name=name,
                value_type=str(raw_spec.get("type", "string") or "string"),
                required=bool(raw_spec.get("required", False)),
                default="" if raw_default is None else str(raw_default),
                default_from="" if raw_default_from is None else str(raw_default_from),
                choices=_string_list(
                    raw_spec.get("choices", []),
                    f"Pattern input choices must be strings: {name}",
                ),
            )
        )
    return tuple(specs)


def _pattern_files_from(raw_files: Any) -> tuple[domain.PatternFile, ...]:
    if raw_files is None:
        return ()
    if not isinstance(raw_files, list):
        raise ValueError("Pattern files must be a list")

    files: list[domain.PatternFile] = []
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise ValueError("Pattern files must be mappings")
        source = raw_file.get("source")
        target = raw_file.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("Pattern files require source and target")
        files.append(domain.PatternFile(_normalize_relative_path(source), target))
    return tuple(files)


def _string_list(value: Any, message: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(message)
    return tuple(value)


__all__ = [
    "FilePatternMaterializer",
    "FilePatternRepository",
    "FilePatternRenderer",
    "current_pattern_root",
    "load_fit_config",
    "normalize_target_path",
]
