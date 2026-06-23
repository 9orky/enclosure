from __future__ import annotations

from pathlib import Path
from typing import Any

from . import errors, facade, manifest

ConfigError = errors.ConfigError
SettingsFacade = facade.SettingsFacade
Manifest = manifest.Manifest


class _LazySettingsFacade:
    def __init__(self) -> None:
        self._facade = None

    def _load(self) -> SettingsFacade:
        if self._facade is None:
            self._facade = SettingsFacade(Manifest(Path.cwd()))
        return self._facade

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)


settings = _LazySettingsFacade()

__all__ = [
    "ConfigError",
    "settings",
]
