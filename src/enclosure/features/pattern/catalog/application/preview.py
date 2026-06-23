from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.scaffolding import Scaffold


def _pattern_for_role(
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


__all__: list[str] = []
