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
            recipe_config=infrastructure.load_recipe_generation_settings(),
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
            recipe_config=infrastructure.load_recipe_generation_settings(),
        ),
    ).generate(recipe_name, target_path, variables=variables)


def write_html_report(
    html_report_path: Path,
    html: str,
) -> None:
    if html_report_path.name.startswith("-"):
        raise ValueError("--html must be a file path, not an option flag")
    html_report_path.parent.mkdir(parents=True, exist_ok=True)
    html_report_path.write_text(html, encoding="utf-8")


__all__ = ["describe_recipe_generation", "generate_recipe", "write_html_report"]
