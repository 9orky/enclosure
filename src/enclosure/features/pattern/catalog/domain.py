from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, TypedDict

from pydantic import Field, field_validator

from enclosure.shared import config


class PatternRole(StrEnum):
    CONTAINER = "container"
    ARCHETYPE = "archetype"
    FRAGMENT = "fragment"


class PatternSlotState(StrEnum):
    ABSENT = "absent"
    FILE = "file"
    PACKAGE = "package"
    SPLIT_FILES = "split-files"
    SPLIT_PACKAGES = "split-packages"


@dataclass(frozen=True)
class PatternSlotName:
    value: str


@dataclass(frozen=True)
class PatternSlot:
    name: PatternSlotName
    state: PatternSlotState
    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternLadder:
    family: str = ""
    rung: str = ""
    slots: tuple[PatternSlot, ...] = ()
    declared: bool = False


@dataclass(frozen=True)
class RelativePath:
    value: Path


class PatternConfig(config.StrictConfigModel):
    skip: tuple[str, ...]
    roles_map: dict[str, str] = Field(default_factory=dict)

    @field_validator("skip")
    @classmethod
    def normalize_skip_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(value.strip().replace("\\", "/") for value in values if value.strip())

    @field_validator("roles_map")
    @classmethod
    def normalize_roles_map(cls, values: dict[str, str]) -> dict[str, str]:
        return {
            module_name.strip().replace("\\", "/"): role_name.strip()
            for module_name, role_name in values.items()
            if module_name.strip() and role_name.strip()
        }

@dataclass(frozen=True)
class PatternCatalogViolation:
    code: str
    message: str
    pattern_name: str = ""


@dataclass(frozen=True)
class PatternCatalogReport:
    pattern_root: Path
    patterns_discovered: int
    patterns_checked: int
    violations: tuple[PatternCatalogViolation, ...] = ()

    def passed(self) -> bool:
        return not self.violations


@dataclass(frozen=True)
class PatternInputSpec:
    name: str
    value_type: str = "string"
    required: bool = False
    default: str = ""
    default_from: str = ""
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternFile:
    source: RelativePath
    target: str


@dataclass(frozen=True)
class Pattern:
    name: str
    root_path: Path
    role: PatternRole
    description: str = ""
    ladder: PatternLadder = field(default_factory=PatternLadder)
    includes: tuple[str, ...] = ()
    archetypes: tuple[str, ...] = ()
    roles_map: dict[str, str] = field(default_factory=dict)
    inputs: tuple[PatternInputSpec, ...] = ()
    files: tuple[PatternFile, ...] = ()


class PatternSummary(TypedDict):
    name: str
    description: str
    role: str
    ladder: dict[str, Any]
    includes: tuple[str, ...]
    archetypes: tuple[str, ...]
    roles_map: dict[str, str]
    inputs: tuple[str, ...]
    files: tuple[str, ...]


def ladder_summary(ladder: PatternLadder) -> dict[str, Any]:
    if not ladder.declared:
        return {}
    return {
        "family": ladder.family,
        "rung": ladder.rung,
        "slots": {
            slot.name.value: {
                "state": slot.state.value,
                "files": slot.files,
                "packages": slot.packages,
            }
            for slot in ladder.slots
        },
    }


__all__ = [
    "Pattern",
    "PatternCatalogReport",
    "PatternCatalogViolation",
    "PatternConfig",
    "PatternFile",
    "PatternInputSpec",
    "PatternLadder",
    "PatternRole",
    "PatternSlot",
    "PatternSlotName",
    "PatternSlotState",
    "PatternSummary",
    "RelativePath",
    "ladder_summary",
]
