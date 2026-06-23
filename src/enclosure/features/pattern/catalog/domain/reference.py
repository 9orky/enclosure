from __future__ import annotations

from typing import Any, TypedDict


class PatternSummary(TypedDict):
    name: str
    description: str
    role: str
    ladder: dict[str, Any]
    includes: tuple[str, ...]
    archetypes: tuple[str, ...]
    roles_map: dict[str, str]
    inputs: tuple[str, ...]
    files: tuple[str, ...]


__all__ = ["PatternSummary"]
