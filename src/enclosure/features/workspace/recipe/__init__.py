from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Mapping

from . import domain

RecipeGenerationConfig = domain.RecipeGenerationConfig
GenerateRecipeResult = domain.GenerateRecipeResult
RecipeCheckReport = domain.RecipeCheckReport
RecipeCheckViolation = domain.RecipeCheckViolation
RecipeBenchAllReport = domain.RecipeBenchAllReport
RecipeBenchContentWeight = domain.RecipeBenchContentWeight
RecipeBenchFileContent = domain.RecipeBenchFileContent
RecipeBenchModule = domain.RecipeBenchModule
RecipeBenchRecurrence = domain.RecipeBenchRecurrence
RecipeBenchReport = domain.RecipeBenchReport
RecipeDrift = domain.RecipeDrift
RecipeDriftReport = domain.RecipeDriftReport
RecipeGenerationReport = domain.RecipeGenerationReport
RecipePreviewFile = domain.RecipePreviewFile
RecipePreviewStatus = domain.RecipePreviewStatus
RecipeSummary = domain.RecipeSummary
parse_variables = domain.parse_variables


def bench_all_preview(
    *,
    recipe_root: Path,
) -> domain.RecipeBenchAllReport:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.bench_all_preview(recipe_root=recipe_root)


def bench_preview(
    module_name: str,
    *,
    recipe_root: Path,
) -> domain.RecipeBenchReport:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.bench_preview(module_name, recipe_root=recipe_root)


def check_recipe_drifts(
    *,
    recipe_root: Path,
) -> domain.RecipeDriftReport:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.check_recipe_drifts(recipe_root=recipe_root)


def check_recipes(
    *,
    recipe_root: Path,
    recipe_name: str | None,
    target_path: Path | str | None,
    variables: Mapping[str, str],
) -> domain.RecipeCheckReport:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.check_recipes(
        recipe_root=recipe_root,
        recipe_name=recipe_name,
        target_path=target_path,
        variables=variables,
    )


def describe_recipe_generation(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.RecipeGenerationReport:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.describe_recipe_generation(
        recipe_name,
        target_path,
        recipe_root=recipe_root,
        variables=variables,
    )


def generate_recipe(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.GenerateRecipeResult:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.generate_recipe(
        recipe_name,
        target_path,
        recipe_root=recipe_root,
        variables=variables,
    )


def list_recipes(
    *,
    recipe_root: Path,
) -> tuple[domain.RecipeSummary, ...]:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.list_recipes(recipe_root=recipe_root)


def show_recipe(
    recipe_name: str,
    *,
    recipe_root: Path,
) -> domain.RecipeSummary | None:
    application = import_module("enclosure.features.workspace.recipe.application")
    return application.show_recipe(recipe_name, recipe_root=recipe_root)

__all__ = [
    "RecipeGenerationConfig",
    "GenerateRecipeResult",
    "RecipeCheckReport",
    "RecipeCheckViolation",
    "RecipeBenchAllReport",
    "RecipeBenchContentWeight",
    "RecipeBenchFileContent",
    "RecipeBenchModule",
    "RecipeBenchRecurrence",
    "RecipeBenchReport",
    "RecipeDrift",
    "RecipeDriftReport",
    "RecipeGenerationReport",
    "RecipePreviewFile",
    "RecipePreviewStatus",
    "RecipeSummary",
    "bench_all_preview",
    "bench_preview",
    "check_recipe_drifts",
    "check_recipes",
    "describe_recipe_generation",
    "generate_recipe",
    "list_recipes",
    "parse_variables",
    "show_recipe",
]
