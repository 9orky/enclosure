from __future__ import annotations

from pathlib import Path

from enclosure.shared import layout


def current_pattern_root() -> Path:
    return layout.current_recipes_root()


__all__ = ["current_pattern_root"]
