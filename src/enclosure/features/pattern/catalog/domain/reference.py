from __future__ import annotations

from typing import Any, TypedDict

from . import manifest


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


def ladder_summary(
    ladder: manifest.PatternLadder,
) -> dict[str, Any]:
    if not ladder.declared:
        return {}
    return {
        "family": ladder.family,
        "rung": ladder.rung,
        "slots": {
            slot.name.value: {
                "state": slot.state.value,
                "files": slot.files,
                "packages": slot.packages,
            }
            for slot in ladder.slots
        },
    }


__all__ = [
    "PatternSummary",
    "ladder_summary",
]
