from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from . import domain, infrastructure


def list_patterns(
    *,
    pattern_root: Path,
) -> tuple[domain.PatternSummary, ...]:
    return tuple(_summarize(pattern) for pattern in _repository(pattern_root).find_all())


def list_current_patterns() -> tuple[domain.PatternSummary, ...]:
    return list_patterns(pattern_root=infrastructure.current_pattern_root())


def show_pattern(
    pattern_name: str,
    *,
    pattern_root: Path,
) -> domain.PatternSummary | None:
    try:
        return _summarize(_repository(pattern_root).get_by_name(pattern_name))
    except LookupError:
        return None


def validate_catalog(
    *,
    pattern_root: Path,
    roles_map: Mapping[str, str],
) -> domain.PatternCatalogReport:
    repository = _repository(pattern_root)
    try:
        patterns = repository.find_all()
    except ValueError as exc:
        return domain.PatternCatalogReport(
            pattern_root=repository.root_path,
            patterns_discovered=0,
            patterns_checked=0,
            violations=(_violation("invalid_manifest", str(exc), ""),),
        )

    patterns_by_name = _patterns_by_name(patterns)
    violations = (
        _catalog_violations(patterns, patterns_by_name)
        + _roles_map_violations(roles_map, patterns_by_name)
    )
    return domain.PatternCatalogReport(
        pattern_root=repository.root_path,
        patterns_discovered=len(patterns),
        patterns_checked=len(patterns),
        violations=violations,
    )


def validate_current_catalog() -> domain.PatternCatalogReport:
    pattern_root = infrastructure.current_pattern_root()
    roles_map = infrastructure.load_pattern_config().roles_map
    return validate_catalog(
        pattern_root=pattern_root,
        roles_map=roles_map,
    )


def composed_ladder_for(
    pattern: domain.Pattern,
    patterns_by_name: Mapping[str, domain.Pattern],
) -> domain.PatternLadder:
    slots_by_name: dict[str, domain.PatternSlot] = {}
    for included_pattern in included_patterns_for(pattern, patterns_by_name, trail=()):
        slots_by_name.update(
            (slot.name.value, slot)
            for slot in included_pattern.ladder.slots
        )
    slots_by_name.update((slot.name.value, slot) for slot in pattern.ladder.slots)
    return domain.PatternLadder(
        family=pattern.ladder.family,
        rung=pattern.ladder.rung,
        slots=tuple(slots_by_name.values()),
        declared=pattern.ladder.declared,
    )


def included_patterns_for(
    pattern: domain.Pattern,
    patterns_by_name: Mapping[str, domain.Pattern],
    *,
    trail: tuple[str, ...],
) -> tuple[domain.Pattern, ...]:
    patterns: list[domain.Pattern] = []
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
    patterns_by_name: Mapping[str, domain.Pattern],
) -> domain.Pattern | None:
    if "+" not in role_name:
        return patterns_by_name.get(role_name)

    include_names = tuple(part.strip() for part in role_name.split("+") if part.strip())
    if (
        not include_names
        or any(include_name not in patterns_by_name for include_name in include_names)
        or any(
            patterns_by_name[include_name].role is domain.PatternRole.CONTAINER
            for include_name in include_names
        )
    ):
        return None
    return domain.Pattern(
        name="composed-role",
        root_path=Path("."),
        role=domain.PatternRole.ARCHETYPE,
        description="Composed Pattern role",
        ladder=domain.PatternLadder(
            family="composed",
            rung=role_name,
            declared=True,
        ),
        includes=include_names,
    )


def _repository(pattern_root: Path) -> infrastructure.FilePatternRepository:
    return infrastructure.FilePatternRepository(pattern_root)


def _patterns_by_name(
    patterns: tuple[domain.Pattern, ...],
) -> dict[str, domain.Pattern]:
    return {pattern.name: pattern for pattern in patterns}


def _summarize(pattern: domain.Pattern) -> domain.PatternSummary:
    return {
        "name": pattern.name,
        "description": pattern.description,
        "role": pattern.role.value,
        "ladder": domain.ladder_summary(pattern.ladder),
        "includes": pattern.includes,
        "archetypes": pattern.archetypes,
        "roles_map": pattern.roles_map,
        "inputs": tuple(input_spec.name for input_spec in pattern.inputs),
        "files": tuple(pattern_file.target for pattern_file in pattern.files),
    }


def _catalog_violations(
    patterns: tuple[domain.Pattern, ...],
    patterns_by_name: Mapping[str, domain.Pattern],
) -> tuple[domain.PatternCatalogViolation, ...]:
    containers = tuple(
        pattern for pattern in patterns if pattern.role is domain.PatternRole.CONTAINER
    )
    if len(containers) != 1:
        code = "missing_container" if not containers else "multiple_containers"
        message = "Pattern catalog must contain exactly one role: container Pattern"
        return (_violation(code, message, ""),)

    container = containers[0]
    if not container.archetypes:
        message = "Container Patterns must declare all contained archetypes"
        return (_violation("missing_container_archetypes", message, container.name),)

    violations: list[domain.PatternCatalogViolation] = []
    for archetype_name in container.archetypes:
        archetype = patterns_by_name.get(archetype_name)
        if archetype is None:
            message = f"Container references missing archetype Pattern {archetype_name}"
            violations.append(
                _violation("missing_archetype_pattern", message, container.name)
            )
        elif archetype.role is not domain.PatternRole.ARCHETYPE:
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
        if pattern.role is domain.PatternRole.ARCHETYPE
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
    patterns: tuple[domain.Pattern, ...],
    patterns_by_name: Mapping[str, domain.Pattern],
) -> tuple[domain.PatternCatalogViolation, ...]:
    violations: list[domain.PatternCatalogViolation] = []
    for pattern in patterns:
        for include_name in pattern.includes:
            included_pattern = patterns_by_name.get(include_name)
            if included_pattern is None:
                violations.append(
                _violation("missing_include_pattern", f"Pattern includes missing Pattern {include_name}", pattern.name)
            )
            elif included_pattern.role is domain.PatternRole.CONTAINER:
                violations.append(
                    _violation(
                        "container_include_pattern",
                        f"Patterns must not include container Pattern {include_name}",
                        pattern.name,
                    )
                )
    return tuple(violations)


def _roles_map_violations(
    roles_map: Mapping[str, str],
    patterns_by_name: Mapping[str, domain.Pattern],
) -> tuple[domain.PatternCatalogViolation, ...]:
    if not roles_map:
        return (
            _violation(
                "missing_roles_map",
                "workspace.recipe.roles_map must declare module Patterns",
                "workspace.recipe.roles_map",
            ),
        )

    violations: list[domain.PatternCatalogViolation] = []
    for module_name, role_name in roles_map.items():
        role_pattern = pattern_for_role(role_name, patterns_by_name)
        if role_pattern is None:
            violations.append(
                _violation(
                    "missing_role_pattern",
                    f"roles_map references missing Pattern {role_name} for {module_name}",
                    "workspace.recipe.roles_map",
                )
            )
        elif "+" not in role_name and role_pattern.role is not domain.PatternRole.ARCHETYPE:
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
) -> domain.PatternCatalogViolation:
    return domain.PatternCatalogViolation(
        code=code,
        message=message,
        pattern_name=pattern_name,
    )


__all__ = [
    "composed_ladder_for",
    "included_patterns_for",
    "list_current_patterns", "list_patterns",
    "pattern_for_role",
    "show_pattern",
    "validate_catalog",
    "validate_current_catalog",
]
