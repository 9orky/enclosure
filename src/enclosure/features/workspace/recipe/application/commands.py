from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .. import domain, infrastructure
from . import generation


def describe_recipe_generation(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.RecipeGenerationReport:
    return generation.RecipeGenerationService(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            config=infrastructure.load_recipe_generation_settings(),
        ),
    ).describe(recipe_name, target_path, variables=variables)


def generate_recipe(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.GenerateRecipeResult:
    return generation.RecipeGenerationService(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            config=infrastructure.load_recipe_generation_settings(),
        ),
    ).generate(recipe_name, target_path, variables=variables)


__all__ = ["describe_recipe_generation", "generate_recipe"]
