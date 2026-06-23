from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from .. import naming

from . import errors, relative_path

_SCAFFOLD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTTED_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SUPPORTED_ROLES = {"container", "archetype", "fragment"}
_SUPPORTED_INPUT_TYPES = {
    "string",
    "identifier",
    "path",
    "dotted_name",
    "slug",
    "choice",
    "list",
}
_SUPPORTED_SLOT_STATES = {
    "absent",
    "file",
    "package",
    "split-files",
    "split-packages",
}


@dataclass(frozen=True)
class RenderedScaffoldFile:
    source_path: Path
    target_path: Path
    relative_path: Path
    content: str


@dataclass(frozen=True)
class Scaffold:
    name: str
    source_root: Path
    role: str
    description: str = ""
    ladder: "_ScaffoldLadder" = field(default_factory=lambda: _ScaffoldLadder())
    includes: tuple[str, ...] = ()
    archetypes: tuple[str, ...] = ()
    roles_map: dict[str, str] = field(default_factory=dict)
    inputs: tuple["_ScaffoldInput", ...] = ()
    files: tuple["_ScaffoldFile", ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self._validate_name(self.name)
        normalized_role = self._validate_role(self.role)
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "source_root", Path(self.source_root))
        object.__setattr__(self, "role", normalized_role)
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "includes", tuple(self.includes))
        object.__setattr__(self, "archetypes", tuple(self.archetypes))
        object.__setattr__(self, "roles_map", dict(self.roles_map))
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(self, "files", tuple(self.files))

    def is_empty(self) -> bool:
        return len(self.files) == 0 and len(self.includes) == 0

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized_name = name.strip()
        if not normalized_name:
            raise errors.ScaffoldError("Scaffold names must not be empty")
        name_path = Path(normalized_name)
        if (
            len(name_path.parts) != 1
            or name_path.parts[0] in {".", ".."}
            or not _SCAFFOLD_NAME_PATTERN.match(normalized_name)
        ):
            raise errors.ScaffoldError("Scaffold names must be a single folder name")
        return normalized_name

    def _validate_role(self, role: str) -> str:
        normalized_role = role.strip()
        if normalized_role not in _SUPPORTED_ROLES:
            raise errors.ScaffoldError(f"Unsupported scaffold role: {role}")
        return normalized_role


@dataclass(frozen=True)
class _ScaffoldInput:
    name: str
    value_type: str = "string"
    required: bool = False
    default: str = ""
    default_from: str = ""
    choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self._validate_name(self.name)
        normalized_type = self._validate_type(self.value_type)
        choices = self._validate_choices(normalized_type, tuple(self.choices))
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "value_type", normalized_type)
        object.__setattr__(self, "choices", choices)

    def _validate_name(self, name: str) -> str:
        normalized_name = name.strip()
        if not _VARIABLE_NAME_PATTERN.match(normalized_name):
            raise errors.ScaffoldError(f"Invalid scaffold input name: {name}")
        return normalized_name

    def _validate_type(self, value_type: str) -> str:
        normalized_type = value_type.strip() or "string"
        if normalized_type not in _SUPPORTED_INPUT_TYPES:
            raise errors.ScaffoldError(
                f"Unsupported input type for {self.name}: {normalized_type}"
            )
        return normalized_type

    def _validate_choices(
        self,
        value_type: str,
        choices: tuple[str, ...],
    ) -> tuple[str, ...]:
        if value_type == "choice" and not choices:
            raise errors.ScaffoldError(f"Choice input must declare choices: {self.name}")
        return choices


@dataclass(frozen=True)
class _ScaffoldFile:
    source: relative_path._ScaffoldRelativePath
    target: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", self._validate_target(self.target))

    def _validate_target(self, target: str) -> str:
        normalized_target = target.strip()
        if not normalized_target:
            raise errors.ScaffoldError("Scaffold files must declare a target")
        return normalized_target


@dataclass(frozen=True)
class _ScaffoldLadder:
    family: str = ""
    rung: str = ""
    slots: tuple["_ScaffoldSlot", ...] = ()
    declared: bool = False

    def __post_init__(self) -> None:
        normalized_family = self._validate_family(self.family, self.declared)
        normalized_rung = self._validate_rung(self.rung, self.declared)
        object.__setattr__(self, "family", normalized_family)
        object.__setattr__(self, "rung", normalized_rung)
        object.__setattr__(self, "slots", tuple(self.slots))

    def is_declared(self) -> bool:
        return self.declared

    def summary(self) -> dict[str, Any]:
        if not self.declared:
            return {}
        return {
            "family": self.family,
            "rung": self.rung,
            "slots": {slot.name: slot.summary() for slot in self.slots},
        }

    def _validate_family(self, family: str, declared: bool) -> str:
        normalized_family = family.strip()
        if declared and not normalized_family:
            raise errors.ScaffoldError("Scaffold ladder family must not be empty")
        return normalized_family

    def _validate_rung(self, rung: str, declared: bool) -> str:
        normalized_rung = rung.strip()
        if declared and not normalized_rung:
            raise errors.ScaffoldError("Scaffold ladder rung must not be empty")
        return normalized_rung


@dataclass(frozen=True)
class _ScaffoldSlot:
    _paths: ClassVar[
        relative_path._ScaffoldRelativePathNormalizer
    ] = relative_path._ScaffoldRelativePathNormalizer()

    name: str
    state: str
    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self._paths.text(self.name, "Scaffold ladder slot name")
        normalized_state = self._validate_state(self.state)
        files = self._normalize_paths(tuple(self.files))
        packages = self._normalize_paths(tuple(self.packages))
        self._validate_split_state(normalized_state, files, packages)

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "state", normalized_state)
        object.__setattr__(self, "files", files)
        object.__setattr__(self, "packages", packages)

    def summary(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "files": self.files,
            "packages": self.packages,
        }

    def _validate_state(self, state: str) -> str:
        normalized_state = state.strip()
        if normalized_state not in _SUPPORTED_SLOT_STATES:
            raise errors.ScaffoldError(
                f"Unsupported scaffold ladder state for {self.name}: {state}"
            )
        return normalized_state

    def _normalize_paths(self, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            self._paths.text(value, "Scaffold ladder slot path")
            for value in values
        )

    def _validate_split_state(
        self,
        state: str,
        files: tuple[str, ...],
        packages: tuple[str, ...],
    ) -> None:
        if state == "split-files" and not files:
            raise errors.ScaffoldError(
                f"Scaffold slot {self.name} must declare files"
            )
        if state == "split-packages" and not packages:
            raise errors.ScaffoldError(
                f"Scaffold slot {self.name} must declare packages"
            )


class _ScaffoldInputValueValidator:
    _paths: ClassVar[
        relative_path._ScaffoldRelativePathNormalizer
    ] = relative_path._ScaffoldRelativePathNormalizer()

    def validate(self, input_spec: _ScaffoldInput, value: str) -> object:
        if input_spec.value_type == "list":
            return self._parse_list(value)

        normalized_value = value.strip()
        self._validate_identifier(input_spec, normalized_value)
        self._validate_dotted_name(input_spec, normalized_value)
        self._validate_path(input_spec, normalized_value)
        self._validate_slug(input_spec, normalized_value)
        self._validate_choice(input_spec, normalized_value)
        return normalized_value

    def _validate_identifier(self, input_spec: _ScaffoldInput, value: str) -> None:
        if input_spec.value_type == "identifier" and not _IDENTIFIER_PATTERN.match(value):
            raise errors.ScaffoldError(
                f"Scaffold variable {input_spec.name} must be an identifier"
            )

    def _validate_dotted_name(self, input_spec: _ScaffoldInput, value: str) -> None:
        if input_spec.value_type == "dotted_name" and not _DOTTED_NAME_PATTERN.match(value):
            raise errors.ScaffoldError(
                f"Scaffold variable {input_spec.name} must be a dotted name"
            )

    def _validate_path(self, input_spec: _ScaffoldInput, value: str) -> None:
        if input_spec.value_type == "path":
            self._paths.normalize(value, "Scaffold variable path")

    def _validate_slug(self, input_spec: _ScaffoldInput, value: str) -> None:
        if input_spec.value_type == "slug" and value != naming.kebab_case(value):
            raise errors.ScaffoldError(
                f"Scaffold variable {input_spec.name} must be a kebab-case slug"
            )

    def _validate_choice(self, input_spec: _ScaffoldInput, value: str) -> None:
        if input_spec.value_type == "choice" and value not in input_spec.choices:
            choices = ", ".join(input_spec.choices)
            raise errors.ScaffoldError(
                f"Scaffold variable {input_spec.name} must be one of: {choices}"
            )

    def _parse_list(self, value: str) -> tuple[str, ...]:
        return tuple(item.strip() for item in value.split(",") if item.strip())
