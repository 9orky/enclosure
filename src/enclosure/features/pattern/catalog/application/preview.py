from __future__ import annotations

from collections.abc import Mapping

from enclosure.shared.scaffolding import catalog_policy
from enclosure.shared.scaffolding import Scaffold


def _pattern_for_role(
    role_name: str,
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> Scaffold | None:
    return catalog_policy.scaffold_for_role(
        role_name,
        patterns_by_name,
        composed_name="composed-role",
        composed_description="Composed Pattern role",
    )


__all__: list[str] = []
