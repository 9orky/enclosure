from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import field_validator

from enclosure.shared import config
from enclosure.shared import naming


class PatternFitConfig(config.StrictConfigModel):
    skip: tuple[str, ...]

    @field_validator("skip")
    @classmethod
    def normalize_skip_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(value.strip().replace("\\", "/") for value in values if value.strip())


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
    source: Path
    target: str


@dataclass(frozen=True)
class Pattern:
    name: str
    root_path: Path
    includes: tuple[str, ...]
    inputs: tuple[PatternInputSpec, ...]
    files: tuple[PatternFile, ...]


class PatternPreviewStatus(StrEnum):
    CREATE = "create"
    SKIP_EXISTS = "skip_exists"
    SKIP_CONFIG = "skip_config"


@dataclass(frozen=True)
class RenderedPatternFile:
    source_path: Path
    target_path: Path
    relative_path: Path
    content: str


@dataclass(frozen=True)
class PatternPreviewFile:
    source_path: Path
    target_path: Path
    relative_path: Path
    status: PatternPreviewStatus
    content: str


@dataclass(frozen=True)
class PatternFitReport:
    pattern_name: str
    project_root: Path
    pattern_found: bool
    pattern_empty: bool
    create_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]
    preview_files: tuple[PatternPreviewFile, ...]


@dataclass(frozen=True)
class MaterializePatternResult:
    pattern_name: str
    project_root: Path
    pattern_found: bool
    pattern_empty: bool
    created_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]


def variable_context_for(value: Any) -> Any:
    if isinstance(value, tuple):
        return value

    text = str(value)
    return {
        "value": text,
        "class": naming.pascal_case(text),
        "pascal": naming.pascal_case(text),
        "camel": naming.camel_case(text),
        "variable": naming.camel_case(text),
        "snake": naming.snake_case(text),
        "kebab": naming.kebab_case(text),
        "slug": naming.kebab_case(text),
        "upper": text.upper(),
        "lower": text.lower(),
        "name": text,
    }


def target_context_for(relative_path: Path) -> dict[str, Any]:
    text = relative_path.as_posix()
    name = relative_path.name
    return {
        "path": text,
        "name": name,
        "class": naming.pascal_case(name),
        "pascal": naming.pascal_case(name),
        "camel": naming.camel_case(name),
        "variable": naming.camel_case(name),
        "snake": naming.snake_case(name),
        "kebab": naming.kebab_case(name),
        "slug": naming.kebab_case(name),
        "parts": relative_path.parts,
        "parent": relative_path.parent.as_posix()
        if relative_path.parent != Path(".")
        else "",
    }


def target_defaults_for(relative_path: Path) -> dict[str, str]:
    target = target_context_for(relative_path)
    return {
        "target_path": target["path"],
        "target_name": target["name"],
        "target_class": target["class"],
        "target_pascal": target["pascal"],
        "target_camel": target["camel"],
        "target_variable": target["variable"],
        "target_snake": target["snake"],
        "target_kebab": target["kebab"],
        "target_slug": target["slug"],
        "target_parent": target["parent"],
    }


__all__ = [
    "MaterializePatternResult",
    "Pattern",
    "PatternFile",
    "PatternFitReport",
    "PatternFitConfig",
    "PatternInputSpec",
    "PatternPreviewFile",
    "PatternPreviewStatus",
    "RenderedPatternFile",
    "target_context_for",
    "target_defaults_for",
    "variable_context_for",
]
