from __future__ import annotations

from collections.abc import Mapping

from enclosure.shared.scaffolding import Scaffold, catalog_policy


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
        composed_ladder=None,
    )


__all__: list[str] = []
