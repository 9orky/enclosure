from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..domain import manifest


class _PatternManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    role: manifest.PatternRole
    description: str = ""
    ladder: dict[str, Any] = Field(default_factory=dict)
    includes: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    roles_map: dict[str, str] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    files: list[dict[str, Any]] = Field(default_factory=list)


def load_pattern_manifest(
    pattern_root: Path,
    manifest_path: Path,
) -> manifest.Pattern:
    raw_data = _load_yaml_mapping(manifest_path)
    return _pattern_from_manifest(pattern_root, manifest_path, raw_data)


def _pattern_from_manifest(
    pattern_root: Path,
    manifest_path: Path,
    raw_data: dict[str, Any],
) -> manifest.Pattern:
    try:
        parsed_manifest = _PatternManifest.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid Pattern manifest: {exc}") from exc

    if parsed_manifest.schema_version != 1:
        raise ValueError(f"Unsupported Pattern schema_version in {manifest_path}")

    return manifest.Pattern(
        name=pattern_root.name,
        root_path=pattern_root,
        description=parsed_manifest.description,
        role=parsed_manifest.role,
        ladder=_pattern_ladder_from(parsed_manifest.ladder),
        includes=_pattern_includes_from(parsed_manifest.includes),
        archetypes=_pattern_archetypes_from(parsed_manifest.archetypes),
        roles_map=parsed_manifest.roles_map,
        inputs=tuple(_input_specs_from(parsed_manifest.inputs)),
        files=tuple(_pattern_files_from(parsed_manifest.files)),
    )


def _input_specs_from(
    raw_inputs: Any,
) -> tuple[manifest.PatternInputSpec, ...]:
    if raw_inputs is None:
        return ()
    if not isinstance(raw_inputs, dict):
        raise ValueError("Pattern inputs must be a mapping")

    specs: list[manifest.PatternInputSpec] = []
    for name, raw_spec in raw_inputs.items():
        if raw_spec is None:
            raw_spec = {}
        if not isinstance(name, str) or not isinstance(raw_spec, dict):
            raise ValueError("Pattern inputs must be named mappings")

        specs.append(
            manifest.PatternInputSpec(
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


def _pattern_files_from(
    raw_files: Any,
) -> tuple[manifest.PatternFile, ...]:
    if raw_files is None:
        return ()
    if not isinstance(raw_files, list):
        raise ValueError("Pattern files must be a list")

    files: list[manifest.PatternFile] = []
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise ValueError("Pattern files must be mappings")
        source = raw_file.get("source")
        target = raw_file.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("Pattern files require source and target")
        files.append(
            manifest.PatternFile(
                manifest.RelativePath(Path(source)),
                target,
            )
        )
    return tuple(files)


def _pattern_archetypes_from(raw_archetypes: Any) -> tuple[str, ...]:
    return _string_list(raw_archetypes, "Pattern archetypes must be strings")


def _pattern_includes_from(raw_includes: Any) -> tuple[str, ...]:
    return _string_list(raw_includes, "Pattern includes must be strings")


def _pattern_ladder_from(
    raw_ladder: Any,
) -> manifest.PatternLadder:
    if raw_ladder == {}:
        return manifest.PatternLadder()
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
    return manifest.PatternLadder(
        family=family,
        rung=rung,
        slots=slots,
        declared=True,
    )


def _pattern_slot_from(
    raw_name: Any,
    raw_slot: Any,
) -> manifest.PatternSlot:
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
        state = manifest.PatternSlotState(raw_state)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported Pattern ladder state for {raw_name}: {raw_state}"
        ) from exc

    return manifest.PatternSlot(
        name=manifest.PatternSlotName(raw_name),
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


__all__ = ["load_pattern_manifest"]
