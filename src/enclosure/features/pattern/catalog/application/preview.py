from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..domain import manifest


def composed_ladder_for(
    pattern: manifest.Pattern,
    patterns_by_name: Mapping[
        str,
        manifest.Pattern,
    ],
) -> manifest.PatternLadder:
    slots_by_name = {}
    for included_pattern in included_patterns_for(pattern, patterns_by_name, trail=()):
        slots_by_name.update(
            (slot.name.value, slot)
            for slot in included_pattern.ladder.slots
        )
    slots_by_name.update((slot.name.value, slot) for slot in pattern.ladder.slots)
    return manifest.PatternLadder(
        family=pattern.ladder.family,
        rung=pattern.ladder.rung,
        slots=tuple(slots_by_name.values()),
        declared=pattern.ladder.declared,
    )


def included_patterns_for(
    pattern: manifest.Pattern,
    patterns_by_name: Mapping[
        str,
        manifest.Pattern,
    ],
    *,
    trail: tuple[str, ...],
) -> tuple[manifest.Pattern, ...]:
    patterns: list[manifest.Pattern] = []
    for include_name in pattern.includes:
        if include_name in trail:
            cycle = " -> ".join(trail + (include_name,))
            raise ValueError(f"Pattern include cycle: {cycle}")
        included_pattern = patterns_by_name.get(include_name)
        if included_pattern is None:
            raise ValueError(f"Pattern include not found: {include_name}")
        patterns.extend(
            included_patterns_for(
                included_pattern,
                patterns_by_name,
                trail=trail + (pattern.name,),
            )
        )
        patterns.append(included_pattern)
    return tuple(patterns)


def pattern_for_role(
    role_name: str,
    patterns_by_name: Mapping[
        str,
        manifest.Pattern,
    ],
) -> manifest.Pattern | None:
    if "+" not in role_name:
        return patterns_by_name.get(role_name)

    include_names = tuple(part.strip() for part in role_name.split("+") if part.strip())
    if (
        not include_names
        or any(include_name not in patterns_by_name for include_name in include_names)
        or any(
            patterns_by_name[
                include_name
            ].role is manifest.PatternRole.CONTAINER
            for include_name in include_names
        )
    ):
        return None
    return manifest.Pattern(
        name="composed-role",
        root_path=Path("."),
        role=manifest.PatternRole.ARCHETYPE,
        description="Composed Pattern role",
        ladder=manifest.PatternLadder(
            family="composed",
            rung=role_name,
            declared=True,
        ),
        includes=include_names,
    )


__all__ = [
    "composed_ladder_for",
    "included_patterns_for",
    "pattern_for_role",
]
