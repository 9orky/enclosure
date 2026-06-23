from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.scaffolding import RenderedScaffoldFile, Scaffold, ScaffoldError
from .. import domain, infrastructure
from . import catalog, drift_ladder, drift_scan

actual_files_for = drift_scan.actual_files_for
drift_files_for = drift_ladder.drift_files_for


class RecipeDriftService:
    def __init__(self, workspace: infrastructure.RecipeWorkspace) -> None:
        self._workspace = workspace

    def build_report(self) -> domain.RecipeDriftReport:
        project_root = self._workspace.project_root()
        violations: list[domain.RecipeCheckViolation] = []
        try:
            recipes = self._workspace.load_recipes()
        except ScaffoldError as exc:
            return domain.RecipeDriftReport(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=Path(),
                modules_checked=0,
                violations=(
                    domain.RecipeCheckViolation(
                        code="invalid_manifest",
                        message=str(exc),
                    ),
                ),
            )

        recipes_by_name = catalog.recipes_by_name(recipes)
        catalog.validate_recipe_catalog(violations, recipes, recipes_by_name)
        subject_root = self._workspace.subject_root()
        roles_map = self._workspace.config().roles_map
        catalog.validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )
        drifts: list[domain.RecipeDrift] = []
        for module_name, role_name in sorted(roles_map.items()):
            role_recipe = catalog.recipe_for_role(role_name, recipes_by_name)
            module_path = subject_root / module_name
            if role_recipe is None:
                continue
            if not module_path.is_dir():
                violations.append(
                    domain.RecipeCheckViolation(
                        code="mapped_module_missing",
                        message=f"Mapped module does not exist: {module_name}",
                        recipe_name="workspace.recipe.roles_map",
                    )
                )
                continue

            try:
                expected_files = expected_files_for(
                    self._workspace,
                    role_recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=self._workspace.subject_target_root() / module_name,
                )
            except ValueError as exc:
                violations.append(
                    domain.RecipeCheckViolation(
                        code="role_render_failed",
                        message=f"{role_name}: {exc}",
                        recipe_name="workspace.recipe.roles_map",
                    )
                )
                continue

            actual_files = actual_files_for(
                module_path,
                project_root=project_root,
                config=self._workspace.config(),
            )
            ladder = catalog.composed_ladder_for(role_recipe, recipes_by_name)
            missing_files, extra_files = drift_files_for(
                role_recipe,
                recipes_by_name=recipes_by_name,
                expected_files=expected_files,
                actual_files=set(actual_files),
            )
            drifts.append(
                domain.RecipeDrift(
                    module_name=module_name,
                    role_name=role_name,
                    ladder_family=ladder.family,
                    ladder_rung=ladder.rung,
                    missing_files=missing_files,
                    extra_files=extra_files,
                )
            )

        return domain.RecipeDriftReport(
            project_root=project_root,
            recipe_root=self._workspace.recipe_root(),
            architecture_root=subject_root,
            modules_checked=len(drifts),
            drifts=tuple(drifts),
            violations=tuple(violations),
        )



def expected_files_for(
    workspace: infrastructure.RecipeWorkspace,
    recipe: Scaffold,
    *,
    recipes_by_name: Mapping[str, Scaffold],
    project_root: Path,
    target_path: Path,
) -> set[str]:
    rendered_files = workspace.render_files(
        recipe,
        recipes_by_name=recipes_by_name,
        project_root=project_root,
        target_path=target_path,
        variables=catalog.sample_variables_for_rendering(recipe, recipes_by_name),
    )
    return set(module_relative_rendered_paths(rendered_files, target_path=target_path))


def module_relative_rendered_paths(
    rendered_files: tuple[RenderedScaffoldFile, ...],
    *,
    target_path: Path | str,
) -> tuple[str, ...]:
    prefix = catalog.relative_path_text(target_path) + "/"
    return tuple(
        sorted(
            rendered_file.relative_path.as_posix().removeprefix(prefix)
            for rendered_file in rendered_files
        )
    )


__all__ = [
    "RecipeDriftService",
    "actual_files_for",
    "drift_files_for",
    "expected_files_for",
    "module_relative_rendered_paths",
]
