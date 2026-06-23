from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .errors import ScaffoldError
from .relative_path import _relative_path
from .scaffold import (
    Scaffold,
    _ScaffoldFile,
    _ScaffoldInput,
    _ScaffoldLadder,
    _ScaffoldSlot,
)


def find_all(scaffold_root: Path) -> tuple[Scaffold, ...]:
    scaffold_root = Path(scaffold_root)
    if not scaffold_root.is_dir():
        return ()
    return tuple(
        _load_scaffold(source_root, _manifest_path(source_root))
        for source_root in sorted(
            _iter_scaffold_roots(scaffold_root),
            key=lambda path: path.name,
        )
    )


def get_by_name(scaffold_root: Path, name: str) -> Scaffold:
    source_root = Path(scaffold_root) / name
    manifest_path = _manifest_path(source_root)
    if not manifest_path.is_file():
        raise LookupError(name)
    return _load_scaffold(source_root, manifest_path)


def _iter_scaffold_roots(scaffold_root: Path):
    for child in scaffold_root.iterdir():
        if child.name.startswith("."):
            continue
        if child.is_dir() and _manifest_path(child).is_file():
            yield child


def _manifest_path(source_root: Path) -> Path:
    return source_root / "recipe.yaml"


def _load_scaffold(source_root: Path, manifest_path: Path) -> Scaffold:
    raw_data = _load_yaml_mapping(manifest_path)
    return _scaffold_from_manifest(source_root, manifest_path, raw_data)


class _ScaffoldManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    role: str
    description: str = ""
    ladder: dict[str, Any] = Field(default_factory=dict)
    includes: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    roles_map: dict[str, str] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    files: list[dict[str, Any]] = Field(default_factory=list)


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ScaffoldError(f"Could not read scaffold manifest: {path}") from exc
    except yaml.YAMLError as exc:
        raise ScaffoldError(f"Invalid scaffold manifest syntax in {path}") from exc

    if not isinstance(raw_data, dict):
        raise ScaffoldError(f"Scaffold manifest must contain a mapping at the top level: {path}")
    return raw_data


def _scaffold_from_manifest(
    source_root: Path,
    manifest_path: Path,
    raw_data: dict[str, Any],
) -> Scaffold:
    try:
        manifest = _ScaffoldManifest.model_validate(raw_data)
    except ValidationError as exc:
        raise ScaffoldError(f"Invalid scaffold manifest: {exc}") from exc

    if manifest.schema_version != 1:
        raise ScaffoldError(f"Unsupported scaffold schema_version in {manifest_path}")

    return Scaffold(
        name=source_root.name,
        source_root=source_root,
        role=manifest.role,
        description=manifest.description,
        ladder=_scaffold_ladder_from(manifest.ladder),
        includes=_string_list(manifest.includes, "Scaffold includes must be strings"),
        archetypes=_string_list(manifest.archetypes, "Scaffold archetypes must be strings"),
        roles_map=manifest.roles_map,
        inputs=_input_specs_from(manifest.inputs),
        files=_scaffold_files_from(manifest.files),
    )


def _input_specs_from(raw_inputs: Any) -> tuple[_ScaffoldInput, ...]:
    if raw_inputs is None:
        return ()
    if not isinstance(raw_inputs, dict):
        raise ScaffoldError("Scaffold inputs must be a mapping")

    specs: list[_ScaffoldInput] = []
    for name, raw_spec in raw_inputs.items():
        if raw_spec is None:
            raw_spec = {}
        if not isinstance(name, str) or not isinstance(raw_spec, dict):
            raise ScaffoldError("Scaffold inputs must be named mappings")

        specs.append(
            _ScaffoldInput(
                name=name,
                value_type=str(raw_spec.get("type", "string") or "string"),
                required=bool(raw_spec.get("required", False)),
                default=_optional_string(raw_spec.get("default")),
                default_from=_optional_string(raw_spec.get("default_from")),
                choices=_string_list(
                    raw_spec.get("choices", []),
                    f"Scaffold input choices must be strings: {name}",
                ),
            )
        )
    return tuple(specs)


def _scaffold_files_from(raw_files: Any) -> tuple[_ScaffoldFile, ...]:
    if raw_files is None:
        return ()
    if not isinstance(raw_files, list):
        raise ScaffoldError("Scaffold files must be a list")

    files: list[_ScaffoldFile] = []
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise ScaffoldError("Scaffold files must be mappings")
        source = raw_file.get("source")
        target = raw_file.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            raise ScaffoldError("Scaffold files require source and target")
        files.append(_ScaffoldFile(_relative_path(source), target))
    return tuple(files)


def _scaffold_ladder_from(raw_ladder: Any) -> _ScaffoldLadder:
    if raw_ladder == {}:
        return _ScaffoldLadder()
    if not isinstance(raw_ladder, dict):
        raise ScaffoldError("Scaffold ladder must be a mapping")

    family = raw_ladder.get("family")
    rung = raw_ladder.get("rung")
    raw_slots = raw_ladder.get("slots", {})
    if not isinstance(family, str) or not isinstance(rung, str):
        raise ScaffoldError("Scaffold ladder requires family and rung")
    if not isinstance(raw_slots, dict):
        raise ScaffoldError("Scaffold ladder slots must be a mapping")

    return _ScaffoldLadder(
        family=family,
        rung=rung,
        slots=tuple(_scaffold_slot_from(name, value) for name, value in raw_slots.items()),
        declared=True,
    )


def _scaffold_slot_from(raw_name: Any, raw_slot: Any) -> _ScaffoldSlot:
    if not isinstance(raw_name, str):
        raise ScaffoldError("Scaffold ladder slot names must be strings")

    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    if isinstance(raw_slot, str):
        raw_state = raw_slot
    elif isinstance(raw_slot, dict):
        raw_state = raw_slot.get("state")
        files = _string_list(
            raw_slot.get("files", []),
            f"Scaffold ladder slot files must be strings: {raw_name}",
        )
        packages = _string_list(
            raw_slot.get("packages", []),
            f"Scaffold ladder slot packages must be strings: {raw_name}",
        )
    else:
        raise ScaffoldError("Scaffold ladder slot values must be strings or mappings")

    if not isinstance(raw_state, str):
        raise ScaffoldError(f"Scaffold ladder slot requires state: {raw_name}")
    return _ScaffoldSlot(
        name=raw_name,
        state=raw_state,
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
        raise ScaffoldError(message)
    return tuple(value)
