from __future__ import annotations

from pathlib import Path

from .base import StrictConfigModel
from .errors import ConfigError
from .facade import SettingsFacade
from .manifest import Manifest

settings = SettingsFacade(Manifest(Path.cwd()))

__all__ = [
    "ConfigError",
    "StrictConfigModel",
    "settings",
]
