from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from enclosure.shared.scaffolding import Scaffold
from .. import domain, infrastructure
from . import catalog_roles, catalog_validation


composed_ladder_for = catalog_roles.composed_ladder_for
composed_recipe_inputs = catalog_roles.composed_recipe_inputs
recipe_for_role = catalog_roles.recipe_for_role
slot_name = catalog_roles.slot_name
slot_state = catalog_roles.slot_state
validate_config_roles_map = catalog_validation.validate_config_roles_map
validate_recipe_catalog = catalog_validation.validate_recipe_catalog

class RecipeCatalog:
    def __init__(self, workspace: infrastructure.RecipeWorkspace) -> None:
        self._workspace = workspace

    def list_recipes(self) -> tuple[domain.RecipeSummary, ...]:
        return tuple(summarize_recipe(recipe) for recipe in self._workspace.load_recipes())

    def show_recipe(self, recipe_name: str) -> domain.RecipeSummary | None:
        recipe = self._workspace.load_recipe(recipe_name)
        if recipe is None:
            return None
        return summarize_recipe(recipe)

    def validate_catalog(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipes: tuple[Scaffold, ...],
        recipes_by_name: Mapping[str, Scaffold],
    ) -> None:
        validate_recipe_catalog(violations, recipes, recipes_by_name)

    def validate_roles_map(
        self,
        violations: list[domain.RecipeCheckViolation],
        *,
        roles_map: Mapping[str, str],
        recipes_by_name: Mapping[str, Scaffold],
    ) -> None:
        validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )

    def recipe_for_role(
        self,
        role_name: str,
        recipes_by_name: Mapping[str, Scaffold],
    ) -> Scaffold | None:
        return recipe_for_role(role_name, recipes_by_name)

    def sample_variables(
        self,
        recipe: Scaffold,
        recipes_by_name: Mapping[str, Scaffold],
    ) -> dict[str, str]:
        return sample_variables_for_rendering(recipe, recipes_by_name)


def summarize_recipe(recipe: Scaffold) -> domain.RecipeSummary:
    return {
        "name": recipe.name,
        "description": recipe.description,
        "role": recipe.role,
        "ladder": recipe.ladder.summary(),
        "includes": recipe.includes,
        "archetypes": recipe.archetypes,
        "roles_map": recipe.roles_map,
        "inputs": tuple(input_spec.name for input_spec in recipe.inputs),
        "files": tuple(recipe_file.target for recipe_file in recipe.files),
    }


def check_variables_for(
    recipe: Scaffold,
    variables: Mapping[str, str],
) -> dict[str, str]:
    check_variables = dict(variables)
    for input_spec in recipe.inputs:
        if input_spec.name in check_variables:
            continue
        if not input_spec.required:
            continue
        check_variables[input_spec.name] = sample_value_for(input_spec)
    return check_variables


def sample_variables_for_rendering(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> dict[str, str]:
    variables: dict[str, str] = {}
    for input_spec in composed_recipe_inputs(recipe, recipes_by_name):
        if not input_spec.required or input_spec.name in variables:
            continue
        variables[input_spec.name] = sample_value_for(input_spec)
    return variables


def sample_value_for(input_spec: Any) -> str:
    if input_spec.choices:
        return input_spec.choices[0]
    if input_spec.value_type == "list":
        return "sample"
    if input_spec.value_type == "path":
        return "sample"
    if input_spec.value_type == "dotted_name":
        return "sample"
    return "sample"


def paths_from_preview_files(
    preview_files: tuple[domain.RecipePreviewFile, ...],
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    create_paths = tuple(
        preview_file.target_path
        for preview_file in preview_files
        if preview_file.status is domain.RecipePreviewStatus.CREATE
    )
    skipped_paths = tuple(
        preview_file.target_path
        for preview_file in preview_files
        if preview_file.status is not domain.RecipePreviewStatus.CREATE
    )
    return create_paths, skipped_paths



def recipes_by_name(recipes: tuple[Scaffold, ...]) -> dict[str, Scaffold]:
    return {recipe.name: recipe for recipe in recipes}


def relative_path_text(path: Path | str) -> str:
    return Path(path).as_posix().strip("/")
__all__ = [
    "RecipeCatalog",
    "check_variables_for",
    "composed_ladder_for",
    "recipe_for_role",
    "recipes_by_name",
    "relative_path_text",
    "sample_variables_for_rendering",
    "slot_name",
    "slot_state",
    "validate_config_roles_map",
    "validate_recipe_catalog",
]
