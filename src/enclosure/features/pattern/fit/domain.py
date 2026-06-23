from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True)
class PatternFitConfig:
    skip: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "skip",
            tuple(
                value.strip().replace("\\", "/")
                for value in self.skip
                if value.strip()
            ),
        )

    @classmethod
    def from_config(cls, value: object) -> PatternFitConfig:
        return cls(skip=tuple(getattr(value, "skip", ())))


class PatternPreviewStatus(StrEnum):
    CREATE = "create"
    SKIP_EXISTS = "skip_exists"
    SKIP_CONFIG = "skip_config"


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


__all__ = [
    "MaterializePatternResult",
    "PatternFitReport",
    "PatternFitConfig",
    "PatternPreviewFile",
    "PatternPreviewStatus",
]
