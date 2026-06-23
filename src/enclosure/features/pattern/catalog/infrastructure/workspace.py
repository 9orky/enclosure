from __future__ import annotations

from pathlib import Path

from enclosure.shared.config import settings


def current_pattern_root() -> Path:
    return settings.metadata.recipes_dir


__all__ = ["current_pattern_root"]
