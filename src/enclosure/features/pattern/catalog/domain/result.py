from __future__ import annotations

from dataclasses import dataclass

from . import manifest


@dataclass(frozen=True)
class PatternRoleResolution:
    role_name: str
    pattern: manifest.Pattern


__all__ = ["PatternRoleResolution"]
