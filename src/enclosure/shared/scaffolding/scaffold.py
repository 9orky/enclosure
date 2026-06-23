from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from enclosure.shared import naming

from .errors import ScaffoldError
from .relative_path import _RelativePath, _relative_path_text, _relative_path_value

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
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ScaffoldError("Scaffold names must not be empty")
        name_path = Path(normalized_name)
        if (
            len(name_path.parts) != 1
            or name_path.parts[0] in {".", ".."}
            or not _SCAFFOLD_NAME_PATTERN.match(normalized_name)
        ):
            raise ScaffoldError("Scaffold names must be a single folder name")

        normalized_role = self.role.strip()
        if normalized_role not in _SUPPORTED_ROLES:
            raise ScaffoldError(f"Unsupported scaffold role: {self.role}")

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


@dataclass(frozen=True)
class _ScaffoldInput:
    name: str
    value_type: str = "string"
    required: bool = False
    default: str = ""
    default_from: str = ""
    choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not _VARIABLE_NAME_PATTERN.match(normalized_name):
            raise ScaffoldError(f"Invalid scaffold input name: {self.name}")

        normalized_type = self.value_type.strip() or "string"
        if normalized_type not in _SUPPORTED_INPUT_TYPES:
            raise ScaffoldError(f"Unsupported input type for {normalized_name}: {normalized_type}")
        if normalized_type == "choice" and not self.choices:
            raise ScaffoldError(f"Choice input must declare choices: {normalized_name}")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "value_type", normalized_type)
        object.__setattr__(self, "choices", tuple(self.choices))


@dataclass(frozen=True)
class _ScaffoldFile:
    source: _RelativePath
    target: str

    def __post_init__(self) -> None:
        normalized_target = self.target.strip()
        if not normalized_target:
            raise ScaffoldError("Scaffold files must declare a target")
        object.__setattr__(self, "target", normalized_target)


@dataclass(frozen=True)
class _ScaffoldLadder:
    family: str = ""
    rung: str = ""
    slots: tuple["_ScaffoldSlot", ...] = ()
    declared: bool = False

    def __post_init__(self) -> None:
        normalized_family = self.family.strip()
        normalized_rung = self.rung.strip()
        if self.declared and not normalized_family:
            raise ScaffoldError("Scaffold ladder family must not be empty")
        if self.declared and not normalized_rung:
            raise ScaffoldError("Scaffold ladder rung must not be empty")

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


@dataclass(frozen=True)
class _ScaffoldSlot:
    name: str
    state: str
    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = _relative_path_text(self.name)
        normalized_state = self.state.strip()
        if normalized_state not in _SUPPORTED_SLOT_STATES:
            raise ScaffoldError(f"Unsupported scaffold ladder state for {normalized_name}: {self.state}")

        files = tuple(_relative_path_text(file_path) for file_path in self.files)
        packages = tuple(_relative_path_text(package_path) for package_path in self.packages)
        if normalized_state == "split-files" and not files:
            raise ScaffoldError(f"Scaffold slot {normalized_name} must declare files")
        if normalized_state == "split-packages" and not packages:
            raise ScaffoldError(f"Scaffold slot {normalized_name} must declare packages")

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


def _validate_input_value(input_spec: _ScaffoldInput, value: str) -> Any:
    if input_spec.value_type == "list":
        return tuple(item.strip() for item in value.split(",") if item.strip())

    normalized_value = value.strip()
    if input_spec.value_type == "identifier" and not _IDENTIFIER_PATTERN.match(normalized_value):
        raise ScaffoldError(f"Scaffold variable {input_spec.name} must be an identifier")
    if input_spec.value_type == "dotted_name" and not _DOTTED_NAME_PATTERN.match(normalized_value):
        raise ScaffoldError(f"Scaffold variable {input_spec.name} must be a dotted name")
    if input_spec.value_type == "path":
        _relative_path_value(normalized_value)
    if input_spec.value_type == "slug" and normalized_value != naming.kebab_case(normalized_value):
        raise ScaffoldError(f"Scaffold variable {input_spec.name} must be a kebab-case slug")
    if input_spec.value_type == "choice" and normalized_value not in input_spec.choices:
        choices = ", ".join(input_spec.choices)
        raise ScaffoldError(f"Scaffold variable {input_spec.name} must be one of: {choices}")
    return normalized_value
