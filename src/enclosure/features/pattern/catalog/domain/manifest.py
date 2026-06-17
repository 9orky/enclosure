from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


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


__all__ = [
    "Pattern",
    "PatternFile",
    "PatternInputSpec",
    "PatternLadder",
    "PatternRole",
    "PatternSlot",
    "PatternSlotName",
    "PatternSlotState",
    "RelativePath",
]
