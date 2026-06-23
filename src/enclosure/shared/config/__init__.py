from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ConfigError
from .facade import SettingsFacade
from .manifest import Manifest


class _LazySettingsFacade:
    def __init__(self) -> None:
        self._facade: SettingsFacade | None = None

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
