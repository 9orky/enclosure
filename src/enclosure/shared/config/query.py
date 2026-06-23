from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ManifestQuery:
    def __init__(self, value: object) -> None:
        self._value = value

    def __getattr__(self, name: str) -> object:
        value = self._selected_value(name)
        return self._wrap(value)

    def select(self, path: str) -> object:
        value: object = self
        for part in self._path_parts(path):
            value = getattr(value, part)
        if isinstance(value, ManifestQuery):
            return value._value
        return value

    def _path_parts(self, path: str) -> tuple[str, ...]:
        parts = tuple(part.strip() for part in path.split(".") if part.strip())
        if not parts:
            raise AttributeError(path)
        return parts

    def _selected_value(self, name: str) -> object:
        if isinstance(self._value, BaseModel):
            if not hasattr(self._value, name):
                raise AttributeError(name)
            return getattr(self._value, name)

        if isinstance(self._value, dict):
            if name not in self._value:
                raise AttributeError(name)
            return self._value[name]

        raise AttributeError(name)

    def _wrap(self, value: object) -> object:
        if isinstance(value, BaseModel):
            return ManifestQuery(value)
        if isinstance(value, dict):
            return ManifestQuery(value)
        if isinstance(value, list):
            return [self._wrap_list_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._wrap_list_value(item) for item in value)
        return value

    def _wrap_list_value(self, value: Any) -> object:
        if isinstance(value, dict):
            return ManifestQuery(value)
        return value


__all__ = ["ManifestQuery"]
