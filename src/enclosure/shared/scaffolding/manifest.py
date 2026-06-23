from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .errors import ScaffoldError
from .relative_path import _ScaffoldRelativePathNormalizer
from .scaffold import (
    Scaffold,
    _ScaffoldFile,
    _ScaffoldInput,
    _ScaffoldLadder,
    _ScaffoldSlot,
)


class _ScaffoldManifestRepository:
    def __init__(self) -> None:
        self._manifest_file_name = "recipe.yaml"
        self._reader = _ScaffoldManifestReader()
        self._converter = _ScaffoldManifestConverter()

    def find_all(self, scaffold_root: Path) -> tuple[Scaffold, ...]:
        scaffold_root = Path(scaffold_root)
        if not scaffold_root.is_dir():
            return ()
        return tuple(
            self._load_scaffold(source_root, self._manifest_path(source_root))
            for source_root in self._iter_scaffold_roots(scaffold_root)
        )

    def get_by_name(self, scaffold_root: Path, name: str) -> Scaffold:
        normalized_name = Scaffold._validate_name(name)
        source_root = Path(scaffold_root) / normalized_name
        manifest_path = self._manifest_path(source_root)
        if not manifest_path.is_file():
            raise LookupError(name)
        return self._load_scaffold(source_root, manifest_path)

    def _iter_scaffold_roots(self, scaffold_root: Path) -> tuple[Path, ...]:
        roots: list[Path] = []
        for child in scaffold_root.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir() and self._manifest_path(child).is_file():
                roots.append(child)
        return tuple(sorted(roots, key=lambda path: path.name))

    def _manifest_path(self, source_root: Path) -> Path:
        return source_root / self._manifest_file_name

    def _load_scaffold(self, source_root: Path, manifest_path: Path) -> Scaffold:
        raw_data = self._reader.read_mapping(manifest_path)
        return self._converter.to_scaffold(source_root, manifest_path, raw_data)


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


class _ScaffoldManifestReader:
    def read_mapping(self, path: Path) -> dict[str, Any]:
        content = self._read_text(path)
        raw_data = self._parse_yaml(path, content)
        return self._validate_mapping(path, raw_data)

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ScaffoldError(f"Could not read scaffold manifest: {path}") from exc

    def _parse_yaml(self, path: Path, content: str) -> object:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:
            raise ScaffoldError(f"Invalid scaffold manifest syntax in {path}") from exc

    def _validate_mapping(self, path: Path, raw_data: object) -> dict[str, Any]:
        if not isinstance(raw_data, dict):
            raise ScaffoldError(f"Scaffold manifest must contain a mapping at the top level: {path}")
        return raw_data


class _ScaffoldManifestConverter:
    def __init__(self) -> None:
        self._paths = _ScaffoldRelativePathNormalizer()

    def to_scaffold(
        self,
        source_root: Path,
        manifest_path: Path,
        raw_data: dict[str, Any],
    ) -> Scaffold:
        try:
            manifest = _ScaffoldManifest.model_validate(raw_data)
        except ValidationError as exc:
            raise ScaffoldError(f"Invalid scaffold manifest: {exc}") from exc

        self._validate_schema_version(manifest, manifest_path)
        return Scaffold(
            name=source_root.name,
            source_root=source_root,
            role=manifest.role,
            description=manifest.description,
            ladder=self._scaffold_ladder_from(manifest.ladder),
            includes=self._string_list(manifest.includes, "Scaffold includes must be strings"),
            archetypes=self._string_list(
                manifest.archetypes,
                "Scaffold archetypes must be strings",
            ),
            roles_map=manifest.roles_map,
            inputs=self._input_specs_from(manifest.inputs),
            files=self._scaffold_files_from(manifest.files),
        )

    def _validate_schema_version(
        self,
        manifest: _ScaffoldManifest,
        manifest_path: Path,
    ) -> None:
        if manifest.schema_version != 1:
            raise ScaffoldError(f"Unsupported scaffold schema_version in {manifest_path}")

    def _input_specs_from(self, raw_inputs: object) -> tuple[_ScaffoldInput, ...]:
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
                    default=self._optional_string(raw_spec.get("default")),
                    default_from=self._optional_string(raw_spec.get("default_from")),
                    choices=self._string_list(
                        raw_spec.get("choices", []),
                        f"Scaffold input choices must be strings: {name}",
                    ),
                )
            )
        return tuple(specs)

    def _scaffold_files_from(self, raw_files: object) -> tuple[_ScaffoldFile, ...]:
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
            files.append(
                _ScaffoldFile(
                    self._paths.relative_path(source, "Scaffold file source"),
                    target,
                )
            )
        return tuple(files)

    def _scaffold_ladder_from(self, raw_ladder: object) -> _ScaffoldLadder:
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
            slots=tuple(
                self._scaffold_slot_from(name, value)
                for name, value in raw_slots.items()
            ),
            declared=True,
        )

    def _scaffold_slot_from(self, raw_name: object, raw_slot: object) -> _ScaffoldSlot:
        if not isinstance(raw_name, str):
            raise ScaffoldError("Scaffold ladder slot names must be strings")

        files: tuple[str, ...] = ()
        packages: tuple[str, ...] = ()
        if isinstance(raw_slot, str):
            raw_state = raw_slot
        elif isinstance(raw_slot, dict):
            raw_state = raw_slot.get("state")
            files = self._string_list(
                raw_slot.get("files", []),
                f"Scaffold ladder slot files must be strings: {raw_name}",
            )
            packages = self._string_list(
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

    def _optional_string(self, value: object) -> str:
        if value is None:
            return ""
        return str(value)

    def _string_list(self, value: object, message: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ScaffoldError(message)
        return tuple(value)
