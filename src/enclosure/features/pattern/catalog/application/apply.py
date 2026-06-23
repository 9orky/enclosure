from __future__ import annotations

from collections.abc import Mapping

from enclosure.shared.scaffolding import Scaffold, catalog_policy

from ..domain import report


def apply_roles_map(
    roles_map: Mapping[str, str],
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> tuple[report.PatternCatalogViolation, ...]:
    return _violations(
        catalog_policy.validate_roles_map(
            roles_map,
            patterns_by_name,
            code_suffix="pattern",
            item_label="Pattern",
            item_plural_label="Patterns",
            subject_name="workspace.recipe.roles_map",
        )
    )


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


def _violations(
    violations: tuple[catalog_policy.CatalogPolicyViolation, ...],
) -> tuple[report.PatternCatalogViolation, ...]:
    return tuple(
        _violation(
            violation.code,
            violation.message,
            violation.subject_name,
        )
        for violation in violations
    )


__all__ = ["apply_roles_map"]
