from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.config import settings
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
        _catalog_violations(patterns, patterns_by_name)
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


def _catalog_violations(
    patterns: tuple[Scaffold, ...],
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> tuple[report.PatternCatalogViolation, ...]:
    containers = tuple(
        pattern
        for pattern in patterns
        if pattern.role == "container"
    )
    if len(containers) != 1:
        code = "missing_container" if not containers else "multiple_containers"
        message = "Pattern catalog must contain exactly one role: container Pattern"
        return (_violation(code, message, ""),)

    container = containers[0]
    if not container.archetypes:
        message = "Container Patterns must declare all contained archetypes"
        return (_violation("missing_container_archetypes", message, container.name),)

    violations: list[report.PatternCatalogViolation] = []
    for archetype_name in container.archetypes:
        archetype = patterns_by_name.get(archetype_name)
        if archetype is None:
            message = f"Container references missing archetype Pattern {archetype_name}"
            violations.append(
                _violation("missing_archetype_pattern", message, container.name)
            )
        elif (
            archetype.role != "archetype"
        ):
            violations.append(
                _violation(
                    "non_archetype_pattern",
                    f"Container archetypes must reference role: archetype Patterns: {archetype_name}",
                    container.name,
                )
            )

    declared_archetypes = set(container.archetypes)
    missing_archetypes = sorted(
        pattern.name
        for pattern in patterns
        if pattern.role == "archetype"
        and pattern.name not in declared_archetypes
    )
    if missing_archetypes:
        violations.append(
            _violation(
                "missing_container_archetype",
                "Container archetypes must include every archetype Pattern: "
                + ", ".join(missing_archetypes),
                container.name,
            )
        )
    return tuple(violations) + _include_violations(patterns, patterns_by_name)


def _include_violations(
    patterns: tuple[Scaffold, ...],
    patterns_by_name: Mapping[
        str,
        Scaffold,
    ],
) -> tuple[report.PatternCatalogViolation, ...]:
    violations: list[report.PatternCatalogViolation] = []
    for pattern in patterns:
        for include_name in pattern.includes:
            included_pattern = patterns_by_name.get(include_name)
            if included_pattern is None:
                violations.append(
                    _violation(
                        "missing_include_pattern",
                        f"Pattern includes missing Pattern {include_name}",
                        pattern.name,
                    )
                )
            elif (
                included_pattern.role == "container"
            ):
                violations.append(
                    _violation(
                        "container_include_pattern",
                        f"Patterns must not include container Pattern {include_name}",
                        pattern.name,
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


__all__ = [
    "validate_catalog",
    "validate_current_catalog",
]
