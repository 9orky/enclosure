from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .. import domain, infrastructure
from . import bench, catalog, drift, generation


def list_recipes(
    *,
    recipe_root: Path,
) -> tuple[domain.RecipeSummary, ...]:
    return catalog.RecipeCatalog(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            recipe_config=domain.RecipeGenerationConfig(skip=()),
        ),
    ).list_recipes()


def show_recipe(
    recipe_name: str,
    *,
    recipe_root: Path,
) -> domain.RecipeSummary | None:
    return catalog.RecipeCatalog(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            recipe_config=domain.RecipeGenerationConfig(skip=()),
        ),
    ).show_recipe(recipe_name)


def check_recipes(
    *,
    recipe_root: Path,
    recipe_name: str | None,
    target_path: Path | str | None,
    variables: Mapping[str, str],
) -> domain.RecipeCheckReport:
    recipe_settings = infrastructure.load_recipe_generation_settings()
    return generation.RecipeGenerationService(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            recipe_config=domain.RecipeGenerationConfig(
                skip=(),
                roles_map=recipe_settings.roles_map,
            ),
        ),
    ).check(
        recipe_name,
        target_path,
        variables=variables,
    )


def check_recipe_drifts(
    *,
    recipe_root: Path,
) -> domain.RecipeDriftReport:
    return drift.RecipeDriftService(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            recipe_config=infrastructure.load_recipe_generation_settings(),
        ),
    ).build_report()


def bench_preview(
    module_name: str,
    *,
    recipe_root: Path,
) -> domain.RecipeBenchReport:
    return bench.RecipeBenchService(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            recipe_config=infrastructure.load_recipe_generation_settings(),
        ),
    ).build_module_report(module_name)


def bench_all_preview(
    *,
    recipe_root: Path,
) -> domain.RecipeBenchAllReport:
    return bench.RecipeBenchService(
        infrastructure.default_workspace(
            recipe_root=recipe_root,
            recipe_config=infrastructure.load_recipe_generation_settings(),
        ),
    ).build_workspace_report()


__all__ = [
    "bench_all_preview",
    "bench_preview",
    "check_recipe_drifts",
    "check_recipes",
    "list_recipes",
    "show_recipe",
]
