from __future__ import annotations

from pathlib import Path

from enclosure.shared.config import settings

from . import domain


def current_pattern_root() -> Path:
    return settings.metadata.recipes_dir


def load_fit_config() -> domain.PatternFitConfig:
    return domain.PatternFitConfig.from_config(settings.query("workspace.recipe"))


__all__ = [
    "current_pattern_root",
    "load_fit_config",
]
