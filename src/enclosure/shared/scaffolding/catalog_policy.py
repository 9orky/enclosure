from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import scaffold


@dataclass(frozen=True)
class CatalogPolicyViolation:
    code: str
    message: str
    subject_name: str = ""


def scaffold_for_role(
    role_name: str,
    scaffolds_by_name: Mapping[str, scaffold.Scaffold],
    *,
    composed_name: str,
    composed_description: str,
    composed_ladder: Any,
) -> scaffold.Scaffold | None:
    if "+" not in role_name:
        return scaffolds_by_name.get(role_name)

    include_names = tuple(part.strip() for part in role_name.split("+") if part.strip())
    if not include_names:
        return None
    if any(include_name not in scaffolds_by_name for include_name in include_names):
        return None
    if any(scaffolds_by_name[include_name].role == "container" for include_name in include_names):
        return None

    scaffold_kwargs: dict[str, object] = {}
    if composed_ladder is not None:
        scaffold_kwargs["ladder"] = composed_ladder
    return scaffold.Scaffold(
        name=composed_name,
        source_root=Path("."),
        role="archetype",
        description=composed_description,
        includes=include_names,
        **scaffold_kwargs,
    )


def validate_scaffold_catalog(
    scaffolds: tuple[scaffold.Scaffold, ...],
    scaffolds_by_name: Mapping[str, scaffold.Scaffold],
    *,
    code_suffix: str,
    catalog_label: str,
    container_label: str,
    item_label: str,
    item_plural_label: str,
) -> tuple[CatalogPolicyViolation, ...]:
    containers = tuple(scaffold for scaffold in scaffolds if scaffold.role == "container")
    if not containers:
        return (
            CatalogPolicyViolation(
                code="missing_container",
                message=f"{catalog_label} must contain exactly one role: {container_label}",
            ),
        )
    if len(containers) > 1:
        return (
            CatalogPolicyViolation(
                code="multiple_containers",
                message=f"{catalog_label} must contain exactly one role: {container_label}",
            ),
        )

    container = containers[0]
    if not container.archetypes:
        return (
            CatalogPolicyViolation(
                code="missing_container_archetypes",
                message=f"Container {item_plural_label} must declare all contained archetypes",
                subject_name=container.name,
            ),
        )

    violations: list[CatalogPolicyViolation] = []
    violations.extend(
        _archetype_violations(
            container,
            scaffolds_by_name,
            code_suffix=code_suffix,
            item_label=item_label,
            item_plural_label=item_plural_label,
        )
    )
    violations.extend(
        _include_violations(
            scaffolds,
            scaffolds_by_name,
            code_suffix=code_suffix,
            item_label=item_label,
            item_plural_label=item_plural_label,
        )
    )

    archetype_names = {scaffold.name for scaffold in scaffolds if scaffold.role == "archetype"}
    missing_archetype_names = tuple(sorted(archetype_names - set(container.archetypes)))
    if missing_archetype_names:
        violations.append(
            CatalogPolicyViolation(
                code="missing_container_archetype",
                message=(
                    f"Container archetypes must include every archetype {item_label}: "
                    + ", ".join(missing_archetype_names)
                ),
                subject_name=container.name,
            )
        )
    return tuple(violations)


def validate_roles_map(
    roles_map: Mapping[str, str],
    scaffolds_by_name: Mapping[str, scaffold.Scaffold],
    *,
    code_suffix: str,
    item_label: str,
    item_plural_label: str,
    subject_name: str,
) -> tuple[CatalogPolicyViolation, ...]:
    if not roles_map:
        return (
            CatalogPolicyViolation(
                code="missing_roles_map",
                message=f"{subject_name} must declare module {item_plural_label}",
                subject_name=subject_name,
            ),
        )

    violations: list[CatalogPolicyViolation] = []
    for module_name, role_name in roles_map.items():
        role_scaffold = scaffold_for_role(
            role_name,
            scaffolds_by_name,
            composed_name="composed-role",
            composed_description=f"Composed {item_label} role",
            composed_ladder=None,
        )
        if role_scaffold is None:
            violations.append(
                CatalogPolicyViolation(
                    code=f"missing_role_{code_suffix}",
                    message=(
                        f"roles_map references missing {item_label} {role_name} "
                        f"for {module_name}"
                    ),
                    subject_name=subject_name,
                )
            )
            continue
        if "+" not in role_name and role_scaffold.role != "archetype":
            violations.append(
                CatalogPolicyViolation(
                    code=f"non_archetype_role_{code_suffix}",
                    message=(
                        f"roles_map must reference archetype {item_plural_label}: "
                        f"{role_name} for {module_name}"
                    ),
                    subject_name=subject_name,
                )
            )
    return tuple(violations)


def _archetype_violations(
    container: scaffold.Scaffold,
    scaffolds_by_name: Mapping[str, scaffold.Scaffold],
    *,
    code_suffix: str,
    item_label: str,
    item_plural_label: str,
) -> tuple[CatalogPolicyViolation, ...]:
    violations: list[CatalogPolicyViolation] = []
    for archetype_name in container.archetypes:
        archetype = scaffolds_by_name.get(archetype_name)
        if archetype is None:
            violations.append(
                CatalogPolicyViolation(
                    code=f"missing_archetype_{code_suffix}",
                    message=f"Container references missing archetype {item_label} {archetype_name}",
                    subject_name=container.name,
                )
            )
            continue
        if archetype.role != "archetype":
            violations.append(
                CatalogPolicyViolation(
                    code=f"non_archetype_{code_suffix}",
                    message=(
                        f"Container archetypes must reference role: archetype "
                        f"{item_plural_label}: {archetype_name}"
                    ),
                    subject_name=container.name,
                )
            )
    return tuple(violations)


def _include_violations(
    scaffolds: tuple[scaffold.Scaffold, ...],
    scaffolds_by_name: Mapping[str, scaffold.Scaffold],
    *,
    code_suffix: str,
    item_label: str,
    item_plural_label: str,
) -> tuple[CatalogPolicyViolation, ...]:
    violations: list[CatalogPolicyViolation] = []
    for candidate in scaffolds:
        for include_name in candidate.includes:
            included_scaffold = scaffolds_by_name.get(include_name)
            if included_scaffold is None:
                violations.append(
                    CatalogPolicyViolation(
                        code=f"missing_include_{code_suffix}",
                        message=f"{item_label} includes missing {item_label} {include_name}",
                        subject_name=candidate.name,
                    )
                )
                continue
            if included_scaffold.role == "container":
                violations.append(
                    CatalogPolicyViolation(
                        code=f"container_include_{code_suffix}",
                        message=(
                            f"{item_plural_label} must not include container "
                            f"{item_label} {include_name}"
                        ),
                        subject_name=candidate.name,
                    )
                )
    return tuple(violations)


__all__ = [
    "CatalogPolicyViolation",
    "scaffold_for_role",
    "validate_roles_map",
    "validate_scaffold_catalog",
]
