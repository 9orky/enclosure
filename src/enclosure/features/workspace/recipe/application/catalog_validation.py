from __future__ import annotations

from collections.abc import Mapping

from enclosure.shared.scaffolding import Scaffold
from .. import domain
from . import catalog_roles


def validate_recipe_catalog(
    violations: list[domain.RecipeCheckViolation],
    recipes: tuple[Scaffold, ...],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    containers = tuple(
        recipe for recipe in recipes if recipe.role == "container"
    )
    if not containers:
        violations.append(
            domain.RecipeCheckViolation(
                code="missing_container",
                message="Recipe catalog must contain exactly one role: container recipe",
            )
        )
        return
    if len(containers) > 1:
        violations.append(
            domain.RecipeCheckViolation(
                code="multiple_containers",
                message="Recipe catalog must contain exactly one role: container recipe",
            )
        )
        return

    container = containers[0]
    if not container.archetypes:
        violations.append(
            domain.RecipeCheckViolation(
                code="missing_container_archetypes",
                message="Container recipes must declare all contained archetypes",
                recipe_name=container.name,
            )
        )
        return
    _validate_archetypes(
        violations,
        recipe_name=container.name,
        archetypes=container.archetypes,
        recipes_by_name=recipes_by_name,
    )
    _validate_includes(violations, recipes, recipes_by_name)
    archetype_names = {
        recipe.name for recipe in recipes if recipe.role == "archetype"
    }
    declared_archetype_names = set(container.archetypes)
    missing_archetype_names = tuple(sorted(archetype_names - declared_archetype_names))
    if missing_archetype_names:
        violations.append(
            domain.RecipeCheckViolation(
                code="missing_container_archetype",
                message=(
                    "Container archetypes must include every archetype recipe: "
                    + ", ".join(missing_archetype_names)
                ),
                recipe_name=container.name,
            )
        )


def validate_config_roles_map(
    violations: list[domain.RecipeCheckViolation],
    *,
    roles_map: Mapping[str, str],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    if not roles_map:
        violations.append(
            domain.RecipeCheckViolation(
                code="missing_roles_map",
                message="workspace.recipe.roles_map must declare module recipes",
                recipe_name="workspace.recipe.roles_map",
            )
        )
        return
    _validate_roles_map(
        violations,
        recipe_name="workspace.recipe.roles_map",
        roles_map=roles_map,
        recipes_by_name=recipes_by_name,
    )


def _validate_includes(
    violations: list[domain.RecipeCheckViolation],
    recipes: tuple[Scaffold, ...],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    for recipe in recipes:
        for include_name in recipe.includes:
            included_recipe = recipes_by_name.get(include_name)
            if included_recipe is None:
                violations.append(
                    domain.RecipeCheckViolation(
                        code="missing_include_recipe",
                        message=f"Recipe includes missing recipe {include_name}",
                        recipe_name=recipe.name,
                    )
                )
                continue
            if included_recipe.role == "container":
                violations.append(
                    domain.RecipeCheckViolation(
                        code="container_include_recipe",
                        message=f"Recipes must not include container recipe {include_name}",
                        recipe_name=recipe.name,
                    )
                )


def _validate_archetypes(
    violations: list[domain.RecipeCheckViolation],
    *,
    recipe_name: str,
    archetypes: tuple[str, ...],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    for archetype_name in archetypes:
        archetype = recipes_by_name.get(archetype_name)
        if archetype is None:
            violations.append(
                domain.RecipeCheckViolation(
                    code="missing_archetype_recipe",
                    message=f"Container references missing archetype recipe {archetype_name}",
                    recipe_name=recipe_name,
                )
            )
            continue
        if archetype.role != "archetype":
            violations.append(
                domain.RecipeCheckViolation(
                    code="non_archetype_recipe",
                    message=(
                        "Container archetypes must reference role: archetype "
                        f"recipes: {archetype_name}"
                    ),
                    recipe_name=recipe_name,
                )
            )


def _validate_roles_map(
    violations: list[domain.RecipeCheckViolation],
    *,
    recipe_name: str,
    roles_map: Mapping[str, str],
    recipes_by_name: Mapping[str, Scaffold],
) -> None:
    for module_name, role_name in roles_map.items():
        role_recipe = catalog_roles.recipe_for_role(role_name, recipes_by_name)
        if role_recipe is None:
            violations.append(
                domain.RecipeCheckViolation(
                    code="missing_role_recipe",
                    message=(
                        f"roles_map references missing recipe {role_name} "
                        f"for {module_name}"
                    ),
                    recipe_name=recipe_name,
                )
            )
            continue
        if "+" not in role_name and role_recipe.role != "archetype":
            violations.append(
                domain.RecipeCheckViolation(
                    code="non_archetype_role_recipe",
                    message=(
                        f"roles_map must reference archetype recipes: {role_name} "
                        f"for {module_name}"
                    ),
                    recipe_name=recipe_name,
                )
            )
            continue


__all__ = [
    "validate_config_roles_map",
    "validate_recipe_catalog",
]
