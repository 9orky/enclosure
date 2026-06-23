from __future__ import annotations

from collections.abc import Mapping

from enclosure.shared.scaffolding import catalog_policy
from enclosure.shared.scaffolding import Scaffold
from .. import domain


def validate_recipe_catalog(
    violations: list[domain.RecipeCheckViolation],
    recipes: tuple[Scaffold, ...],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    violations.extend(
        _recipe_violations(
            catalog_policy.validate_scaffold_catalog(
                recipes,
                recipes_by_name,
                code_suffix="recipe",
                catalog_label="Recipe catalog",
                container_label="container recipe",
                item_label="recipe",
                item_plural_label="recipes",
            )
        )
    )


def validate_config_roles_map(
    violations: list[domain.RecipeCheckViolation],
    *,
    roles_map: Mapping[str, str],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    violations.extend(
        _recipe_violations(
            catalog_policy.validate_roles_map(
                roles_map,
                recipes_by_name,
                code_suffix="recipe",
                item_label="recipe",
                item_plural_label="recipes",
                subject_name="workspace.recipe.roles_map",
            )
        )
    )


def _recipe_violations(
    violations: tuple[catalog_policy.CatalogPolicyViolation, ...],
) -> tuple[domain.RecipeCheckViolation, ...]:
    return tuple(
        domain.RecipeCheckViolation(
            code=violation.code,
            message=violation.message,
            recipe_name=violation.subject_name,
        )
        for violation in violations
    )


__all__ = [
    "validate_config_roles_map",
    "validate_recipe_catalog",
]
