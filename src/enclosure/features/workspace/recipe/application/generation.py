from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.scaffolding import RenderedScaffoldFile, Scaffold, ScaffoldError
from .. import domain, infrastructure
from . import catalog


class RecipeGenerationService:
    def __init__(self, workspace: infrastructure.RecipeWorkspace) -> None:
        self._workspace = workspace

    def check(
        self,
        recipe_name: str | None,
        target_path: Path | str | None,
        *,
        variables: Mapping[str, str],
    ) -> domain.RecipeCheckReport:
        project_root = self._workspace.project_root()
        violations: list[domain.RecipeCheckViolation] = []

        try:
            recipes = self._workspace.load_recipes()
        except ScaffoldError as exc:
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                recipes_discovered=0,
                recipes_checked=0,
                rendered_paths_checked=0,
                violations=(
                    domain.RecipeCheckViolation(
                        code="invalid_manifest",
                        message=str(exc),
                        recipe_name=recipe_name or "",
                    ),
                ),
            )

        if recipe_name is None:
            rendered_paths_checked = 0
            recipes_by_name = catalog.recipes_by_name(recipes)
            catalog.validate_recipe_catalog(violations, recipes, recipes_by_name)
            catalog.validate_config_roles_map(
                violations,
                roles_map=self._workspace.config().roles_map,
                recipes_by_name=recipes_by_name,
            )
            for recipe in recipes:
                rendered_paths_checked += self._check_recipe(
                    violations,
                    recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=Path("_enclosure_recipe_check") / recipe.name,
                    variables=catalog.check_variables_for(recipe, variables),
                )
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                recipes_discovered=len(recipes),
                recipes_checked=len(recipes),
                rendered_paths_checked=rendered_paths_checked,
                violations=tuple(violations),
            )

        recipe = self._workspace.load_recipe(recipe_name)
        if recipe is None:
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                recipes_discovered=len(recipes),
                recipes_checked=0,
                rendered_paths_checked=0,
                violations=(
                    domain.RecipeCheckViolation(
                        code="recipe_not_found",
                        message=f"Recipe not found: {recipe_name}",
                        recipe_name=recipe_name or "",
                    ),
                ),
            )

        recipes_by_name = catalog.recipes_by_name(recipes)
        catalog.validate_recipe_catalog(violations, recipes, recipes_by_name)
        catalog.validate_config_roles_map(
            violations,
            roles_map=self._workspace.config().roles_map,
            recipes_by_name=recipes_by_name,
        )
        rendered_paths_checked = self._check_recipe(
            violations,
            recipe,
            recipes_by_name=recipes_by_name,
            project_root=project_root,
            target_path=target_path or Path("_enclosure_recipe_check") / recipe.name,
            variables=catalog.check_variables_for(recipe, variables),
        )

        return domain.RecipeCheckReport(
            project_root=project_root,
            recipe_root=self._workspace.recipe_root(),
            recipes_discovered=len(recipes),
            recipes_checked=1,
            rendered_paths_checked=rendered_paths_checked,
            violations=tuple(violations),
        )

    def _check_recipe(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipe: Scaffold,
        *,
        recipes_by_name: Mapping[str, Scaffold],
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> int:
        self._validate_recipe_contract(violations, recipe, recipes_by_name)
        try:
            rendered_files = self._workspace.render_files(
                recipe,
                recipes_by_name=recipes_by_name,
                project_root=project_root,
                target_path=target_path,
                variables=variables,
            )
        except ValueError as exc:
            violations.append(
                domain.RecipeCheckViolation(
                    code="render_failed",
                    message=str(exc),
                    recipe_name=recipe.name,
                )
            )
            return 0

        create_paths, skipped_paths = self._plan_paths(rendered_files)
        return len(create_paths) + len(skipped_paths)

    def describe(
        self,
        recipe_name: str,
        target_path: Path | str,
        *,
        variables: Mapping[str, str],
    ) -> domain.RecipeGenerationReport:
        project_root = self._workspace.project_root()
        recipe = self._workspace.load_recipe(recipe_name)
        if recipe is None:
            return {
                "recipe_name": recipe_name,
                "project_root": project_root,
                "recipe_found": False,
                "recipe_empty": False,
                "create_paths": (),
                "skipped_paths": (),
                "preview_files": (),
            }
        recipes_by_name = catalog.recipes_by_name(self._workspace.load_recipes())

        rendered_files = self._workspace.render_files(
            recipe,
            recipes_by_name=recipes_by_name,
            project_root=project_root,
            target_path=target_path,
            variables=variables,
        )
        preview_files = self._plan_preview_files(rendered_files)
        create_paths, skipped_paths = catalog.paths_from_preview_files(preview_files)
        return {
            "recipe_name": recipe.name,
            "project_root": project_root,
            "recipe_found": True,
            "recipe_empty": recipe.is_empty(),
            "create_paths": create_paths,
            "skipped_paths": skipped_paths,
            "preview_files": preview_files,
        }

    def generate(
        self,
        recipe_name: str,
        target_path: Path | str,
        *,
        variables: Mapping[str, str],
    ) -> domain.GenerateRecipeResult:
        project_root = self._workspace.project_root()
        recipe = self._workspace.load_recipe(recipe_name)
        if recipe is None:
            return {
                "recipe_name": recipe_name,
                "project_root": project_root,
                "recipe_found": False,
                "recipe_empty": False,
                "created_paths": (),
                "skipped_paths": (),
            }
        recipes_by_name = catalog.recipes_by_name(self._workspace.load_recipes())

        rendered_files = self._workspace.render_files(
            recipe,
            recipes_by_name=recipes_by_name,
            project_root=project_root,
            target_path=target_path,
            variables=variables,
        )
        create_paths, skipped_paths = self._plan_paths(rendered_files)
        self._workspace.write_files(rendered_files, create_paths=create_paths)

        return {
            "recipe_name": recipe.name,
            "project_root": project_root,
            "recipe_found": True,
            "recipe_empty": recipe.is_empty(),
            "created_paths": create_paths,
            "skipped_paths": skipped_paths,
        }


    def _plan_paths(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
    ) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
        return catalog.paths_from_preview_files(self._plan_preview_files(rendered_files))

    def _plan_preview_files(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
    ) -> tuple[domain.RecipePreviewFile, ...]:
        preview_files: list[domain.RecipePreviewFile] = []
        for rendered_file in rendered_files:
            target_path = rendered_file.target_path
            relative_path = rendered_file.relative_path
            if self._workspace.config().should_skip(relative_path):
                status = domain.RecipePreviewStatus.SKIP_CONFIG
            elif target_path.exists():
                status = domain.RecipePreviewStatus.SKIP_EXISTS
            else:
                status = domain.RecipePreviewStatus.CREATE

            preview_files.append(
                domain.RecipePreviewFile(
                    source_path=rendered_file.source_path,
                    target_path=target_path,
                    relative_path=relative_path,
                    status=status,
                    content=rendered_file.content,
                )
            )

        return tuple(preview_files)

    def _validate_recipe_contract(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipe: Scaffold,
        recipes_by_name: Mapping[str, Scaffold],
    ) -> None:
        if recipe.roles_map:
            violations.append(
                domain.RecipeCheckViolation(
                    code="unexpected_roles_map",
                    message="Recipe manifests must not declare roles_map; use workspace.recipe.roles_map",
                    recipe_name=recipe.name,
                )
            )
            return
        if recipe.role in {"archetype", "fragment"} and not recipe.ladder.is_declared():
            violations.append(
                domain.RecipeCheckViolation(
                    code="missing_ladder",
                    message="Archetype and fragment recipes must declare ladder metadata",
                    recipe_name=recipe.name,
                )
            )
            return
        if recipe.role == "archetype" and recipe.archetypes:
            violations.append(
                domain.RecipeCheckViolation(
                    code="unexpected_archetypes",
                    message="Only container recipes may declare archetypes",
                    recipe_name=recipe.name,
                )
            )
            return


__all__ = ["RecipeGenerationService"]
