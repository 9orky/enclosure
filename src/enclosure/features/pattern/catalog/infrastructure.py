from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError

from enclosure.shared import config, layout

from . import domain


class _PatternManifest(config.StrictConfigModel):
    schema_version: int
    role: domain.PatternRole
    description: str = ""
    ladder: dict[str, Any] = Field(default_factory=dict)
    includes: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    roles_map: dict[str, str] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    files: list[dict[str, Any]] = Field(default_factory=list)


def current_pattern_root() -> Path:
    return layout.current_recipes_root()


def load_pattern_config() -> domain.PatternConfig:
    _project_root, config_path, raw_data = config.load_project_mapping()
    return config.section(
        raw_data,
        "workspace.recipe",
        domain.PatternConfig,
        config_path,
    )


class FilePatternRepository:
    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def find_all(self) -> tuple[domain.Pattern, ...]:
        if not self.root_path.is_dir():
            return ()

        return tuple(
            self._load_pattern(pattern_root, layout.recipe_manifest_path(pattern_root))
            for pattern_root in sorted(
                self._iter_pattern_roots(),
                key=lambda path: path.name,
            )
        )

    def get_by_name(self, name: str) -> domain.Pattern:
        pattern_root = self.root_path / name
        manifest_path = layout.recipe_manifest_path(pattern_root)
        if not manifest_path.is_file():
            raise LookupError(name)

        return self._load_pattern(pattern_root, manifest_path)

    def _iter_pattern_roots(self):
        for child in self.root_path.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir() and layout.recipe_manifest_path(child).is_file():
                yield child

    def _load_pattern(self, pattern_root: Path, manifest_path: Path) -> domain.Pattern:
        raw_data = config.load_yaml_mapping(
            manifest_path,
            label="Pattern manifest",
            error_type=ValueError,
        )
        return _pattern_from_manifest(pattern_root, manifest_path, raw_data)


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
        description=manifest.description,
        role=manifest.role,
        ladder=_pattern_ladder_from(manifest.ladder),
        includes=_pattern_includes_from(manifest.includes),
        archetypes=_pattern_archetypes_from(manifest.archetypes),
        roles_map=manifest.roles_map,
        inputs=tuple(_input_specs_from(manifest.inputs)),
        files=tuple(_pattern_files_from(manifest.files)),
    )


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

        specs.append(
            domain.PatternInputSpec(
                name=name,
                value_type=str(raw_spec.get("type", "string") or "string"),
                required=bool(raw_spec.get("required", False)),
                default=_optional_string(raw_spec.get("default")),
                default_from=_optional_string(raw_spec.get("default_from")),
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
        files.append(domain.PatternFile(domain.RelativePath(Path(source)), target))
    return tuple(files)


def _pattern_archetypes_from(raw_archetypes: Any) -> tuple[str, ...]:
    return _string_list(raw_archetypes, "Pattern archetypes must be strings")


def _pattern_includes_from(raw_includes: Any) -> tuple[str, ...]:
    return _string_list(raw_includes, "Pattern includes must be strings")


def _pattern_ladder_from(raw_ladder: Any) -> domain.PatternLadder:
    if raw_ladder == {}:
        return domain.PatternLadder()
    if not isinstance(raw_ladder, dict):
        raise ValueError("Pattern ladder must be a mapping")

    family = raw_ladder.get("family")
    rung = raw_ladder.get("rung")
    raw_slots = raw_ladder.get("slots", {})
    if not isinstance(family, str) or not isinstance(rung, str):
        raise ValueError("Pattern ladder requires family and rung")
    if not isinstance(raw_slots, dict):
        raise ValueError("Pattern ladder slots must be a mapping")

    slots = tuple(_pattern_slot_from(name, value) for name, value in raw_slots.items())
    return domain.PatternLadder(
        family=family,
        rung=rung,
        slots=slots,
        declared=True,
    )


def _pattern_slot_from(raw_name: Any, raw_slot: Any) -> domain.PatternSlot:
    if not isinstance(raw_name, str):
        raise ValueError("Pattern ladder slot names must be strings")

    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    if isinstance(raw_slot, str):
        raw_state = raw_slot
    elif isinstance(raw_slot, dict):
        raw_state = raw_slot.get("state")
        files = _string_list(
            raw_slot.get("files", []),
            f"Pattern ladder slot files must be strings: {raw_name}",
        )
        packages = _string_list(
            raw_slot.get("packages", []),
            f"Pattern ladder slot packages must be strings: {raw_name}",
        )
    else:
        raise ValueError("Pattern ladder slot values must be strings or mappings")

    if not isinstance(raw_state, str):
        raise ValueError(f"Pattern ladder slot requires state: {raw_name}")
    try:
        state = domain.PatternSlotState(raw_state)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported Pattern ladder state for {raw_name}: {raw_state}"
        ) from exc

    return domain.PatternSlot(
        name=domain.PatternSlotName(raw_name),
        state=state,
        files=files,
        packages=packages,
    )


def _optional_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _string_list(value: Any, message: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(message)
    return tuple(value)


__all__ = [
    "FilePatternRepository",
    "current_pattern_root",
    "load_pattern_config",
]
