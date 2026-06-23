from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from enclosure.shared.scaffolding import Scaffold, scaffolding


def composed_ladder_for(
    pattern: Scaffold,
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> dict[str, Any]:
    slots_by_name: dict[str, Any] = {}
    for composed_pattern in scaffolding.compose(pattern, tuple(patterns_by_name.values())):
        for slot in composed_pattern.ladder.slots:
            slots_by_name[slot.name] = slot.summary()
    if not pattern.ladder.is_declared() and not slots_by_name:
        return {}
    return {
        "family": _ladder_family_for(pattern),
        "rung": _ladder_rung_for(pattern),
        "slots": slots_by_name,
    }


def pattern_for_role(
    role_name: str,
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> Scaffold | None:
    if "+" not in role_name:
        return patterns_by_name.get(role_name)

    include_names = tuple(part.strip() for part in role_name.split("+") if part.strip())
    if (
        not include_names
        or any(include_name not in patterns_by_name for include_name in include_names)
        or any(
            patterns_by_name[
                include_name
            ].role == "container"
            for include_name in include_names
        )
    ):
        return None
    return Scaffold(
        name="composed-role",
        source_root=Path("."),
        role="archetype",
        description="Composed Pattern role",
        includes=include_names,
    )


def _ladder_family_for(pattern: Scaffold) -> str:
    if pattern.name == "composed-role":
        return "composed"
    return pattern.ladder.family


def _ladder_rung_for(pattern: Scaffold) -> str:
    if pattern.name == "composed-role":
        return "+".join(pattern.includes)
    return pattern.ladder.rung


__all__ = [
    "composed_ladder_for",
    "pattern_for_role",
]
