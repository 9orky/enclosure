from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.config import settings
from enclosure.shared.scaffolding import (
    RenderedScaffoldFile,
    Scaffold,
    scaffolding,
)

from . import domain


class RecipeWorkspace:
    def __init__(
        self,
        *,
        project_root: Path,
        recipe_root: Path,
        subject_root: Path,
        config: domain.RecipeGenerationConfig,
    ) -> None:
        self._project_root = Path(project_root).resolve()
        self._recipe_root = Path(recipe_root)
        self._subject_root = Path(subject_root)
        self._config = config

    def project_root(self) -> Path:
        return self._project_root

    def recipe_root(self) -> Path:
        return self._recipe_root

    def subject_root(self) -> Path:
        return self._subject_root

    def subject_target_root(self) -> Path:
        return self._subject_root.relative_to(self._project_root)

    def config(self) -> domain.RecipeGenerationConfig:
        return self._config

    def load_recipes(self) -> tuple[Scaffold, ...]:
        return scaffolding.load_all(self._recipe_root)

    def load_recipe(self, recipe_name: str) -> Scaffold | None:
        try:
            return scaffolding.load(self._recipe_root, recipe_name)
        except LookupError:
            return None

    def render_files(
        self,
        recipe: Scaffold,
        *,
        recipes_by_name: Mapping[str, Scaffold],
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> tuple[RenderedScaffoldFile, ...]:
        return scaffolding.render(
            recipe,
            tuple(recipes_by_name.values()),
            project_root,
            target_path,
            dict(variables),
        )

    def write_files(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
        *,
        create_paths: tuple[Path, ...],
    ) -> None:
        scaffolding.write(rendered_files, create_paths=create_paths)


def compose_recipes(
    recipe: Scaffold,
    recipes: tuple[Scaffold, ...],
) -> tuple[Scaffold, ...]:
    return scaffolding.compose(recipe, recipes)


def recipe_command_context() -> domain.RecipeCommandContext:
    return domain.RecipeCommandContext(
        project_root=settings.metadata.project_root,
        recipe_root=settings.metadata.recipes_dir,
    )


def default_workspace(
    *,
    recipe_root: Path,
    config: domain.RecipeGenerationConfig,
) -> RecipeWorkspace:
    return RecipeWorkspace(
        project_root=settings.metadata.project_root,
        recipe_root=recipe_root,
        subject_root=settings.architecture_root(),
        config=config,
    )


def load_recipe_generation_settings() -> domain.RecipeGenerationConfig:
    recipe_settings = settings.query("workspace.recipe")
    if not isinstance(recipe_settings, domain.RecipeGenerationConfig):
        raise RuntimeError("workspace.recipe settings were not validated")
    return recipe_settings


__all__ = [
    "RecipeWorkspace",
    "compose_recipes",
    "default_workspace",
    "load_recipe_generation_settings",
    "recipe_command_context",
]
