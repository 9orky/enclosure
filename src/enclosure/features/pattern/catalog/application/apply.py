from __future__ import annotations

from collections.abc import Mapping

from enclosure.shared.scaffolding import Scaffold

from ..domain import report
from . import preview


def apply_roles_map(
    roles_map: Mapping[str, str],
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> tuple[report.PatternCatalogViolation, ...]:
    if not roles_map:
        return (
            _violation(
                "missing_roles_map",
                "workspace.recipe.roles_map must declare module Patterns",
                "workspace.recipe.roles_map",
            ),
        )

    violations: list[report.PatternCatalogViolation] = []
    for module_name, role_name in roles_map.items():
        role_pattern = preview._pattern_for_role(
            role_name,
            patterns_by_name,
        )
        if role_pattern is None:
            violations.append(
                _violation(
                    "missing_role_pattern",
                    f"roles_map references missing Pattern {role_name} for {module_name}",
                    "workspace.recipe.roles_map",
                )
            )
        elif (
            "+" not in role_name
            and role_pattern.role != "archetype"
        ):
            violations.append(
                _violation(
                    "non_archetype_role_pattern",
                    f"roles_map must reference archetype Patterns: {role_name} for {module_name}",
                    "workspace.recipe.roles_map",
                )
            )
    return tuple(violations)


def _violation(
    code: str,
    message: str,
    pattern_name: str,
) -> report.PatternCatalogViolation:
    return report.PatternCatalogViolation(
        code=code,
        message=message,
        pattern_name=pattern_name,
    )


__all__ = ["apply_roles_map"]
