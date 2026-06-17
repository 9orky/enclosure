from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CatalogPatternContext:
    project_root: Path
    pattern_root: Path
    module_path: str


__all__ = ["CatalogPatternContext"]
