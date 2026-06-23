from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.config import settings
from enclosure.shared.scaffolding import catalog_policy
from enclosure.shared.scaffolding import Scaffold, ScaffoldError, scaffolding

from ..domain import report
from ..infrastructure import workspace
from . import apply


def validate_catalog(
    *,
    pattern_root: Path,
    roles_map: Mapping[str, str],
) -> report.PatternCatalogReport:
    try:
        patterns = scaffolding.load_all(pattern_root)
    except ScaffoldError as exc:
        return report.PatternCatalogReport(
            pattern_root=pattern_root,
            patterns_discovered=0,
            patterns_checked=0,
            violations=(_violation("invalid_manifest", str(exc), ""),),
        )

    patterns_by_name = _patterns_by_name(patterns)
    violations = (
        _violations(
            catalog_policy.validate_scaffold_catalog(
                patterns,
                patterns_by_name,
                code_suffix="pattern",
                catalog_label="Pattern catalog",
                container_label="container Pattern",
                item_label="Pattern",
                item_plural_label="Patterns",
            )
        )
        + apply.apply_roles_map(
            roles_map,
            patterns_by_name,
        )
    )
    return report.PatternCatalogReport(
        pattern_root=pattern_root,
        patterns_discovered=len(patterns),
        patterns_checked=len(patterns),
        violations=violations,
    )


def validate_current_catalog() -> report.PatternCatalogReport:
    pattern_root = workspace.current_pattern_root()
    roles_map = getattr(settings.query("workspace.recipe"), "roles_map", {})
    return validate_catalog(
        pattern_root=pattern_root,
        roles_map=roles_map,
    )


def _patterns_by_name(
    patterns: tuple[Scaffold, ...],
) -> dict[str, Scaffold]:
    return {pattern.name: pattern for pattern in patterns}


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


__all__ = [
    "validate_catalog",
    "validate_current_catalog",
]
