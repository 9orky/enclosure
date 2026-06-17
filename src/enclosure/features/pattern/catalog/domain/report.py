from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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


__all__ = [
    "PatternCatalogReport",
    "PatternCatalogViolation",
]
