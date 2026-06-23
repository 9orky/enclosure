from __future__ import annotations

from pathlib import Path

from enclosure.shared.scaffolding import ScaffoldError
from .. import domain, infrastructure
from . import bench_content, bench_signals, catalog, drift

bench_all_classification = bench_signals.bench_all_classification
bench_classification = bench_signals.bench_classification
bench_modules_with_content_weights = bench_content.bench_modules_with_content_weights
bench_recurrence_for = bench_signals.bench_recurrence_for
module_file_contents = bench_content.module_file_contents
reports_by_role = bench_signals.reports_by_role


class RecipeBenchService:
    def __init__(self, workspace: infrastructure.RecipeWorkspace) -> None:
        self._workspace = workspace

    def build_module_report(self, module_name: str) -> domain.RecipeBenchReport:
        project_root = self._workspace.project_root()
        selected_module = module_name.strip().replace("\\", "/")
        violations: list[domain.RecipeCheckViolation] = []
        try:
            recipes = self._workspace.load_recipes()
        except ScaffoldError as exc:
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=Path(),
                selected_module=selected_module,
                role_name="",
                violation=domain.RecipeCheckViolation(
                    code="invalid_manifest",
                    message=str(exc),
                ),
            )

        recipes_by_name = catalog.recipes_by_name(recipes)
        catalog.validate_recipe_catalog(violations, recipes, recipes_by_name)
        roles_map = self._workspace.config().roles_map
        catalog.validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )

        subject_root = self._workspace.subject_root()
        role_name = roles_map.get(selected_module, "")
        if not role_name:
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=subject_root,
                selected_module=selected_module,
                role_name="",
                violation=domain.RecipeCheckViolation(
                    code="module_unmapped",
                    message=(
                        "Module is not mapped in workspace.recipe.roles_map: "
                        f"{selected_module}"
                    ),
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        role_recipe = catalog.recipe_for_role(role_name, recipes_by_name)
        if role_recipe is None:
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=subject_root,
                selected_module=selected_module,
                role_name=role_name,
                violation=domain.RecipeCheckViolation(
                    code="missing_role_recipe",
                    message=(
                        f"roles_map references missing recipe {role_name} "
                        f"for {selected_module}"
                    ),
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        selected_path = subject_root / selected_module
        if not selected_path.is_dir():
            return empty_bench_report(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=subject_root,
                selected_module=selected_module,
                role_name=role_name,
                violation=domain.RecipeCheckViolation(
                    code="mapped_module_missing",
                    message=f"Mapped module does not exist: {selected_module}",
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        same_role_module_names = tuple(
            sorted(
                candidate_module
                for candidate_module, candidate_role in roles_map.items()
                if candidate_role == role_name
            )
        )
        modules: list[domain.RecipeBenchModule] = []
        for candidate_module in same_role_module_names:
            module_path = subject_root / candidate_module
            if not module_path.is_dir():
                violations.append(
                    domain.RecipeCheckViolation(
                        code="mapped_module_missing",
                        message=f"Mapped module does not exist: {candidate_module}",
                        recipe_name="workspace.recipe.roles_map",
                    )
                )
                continue

            target_path = self._workspace.subject_target_root() / candidate_module
            try:
                rendered_files = self._workspace.render_files(
                    role_recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=target_path,
                    variables=catalog.sample_variables_for_rendering(
                        role_recipe,
                        recipes_by_name,
                    ),
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

            expected_files = drift.module_relative_rendered_paths(
                rendered_files,
                target_path=target_path,
            )
            actual_files = drift.actual_files_for(
                module_path,
                project_root=project_root,
                config=self._workspace.config(),
            )
            missing_files, residue_files = drift.drift_files_for(
                role_recipe,
                recipes_by_name=recipes_by_name,
                expected_files=set(expected_files),
                actual_files=set(actual_files),
            )
            slot_growth_files = tuple(
                sorted(set(actual_files) - set(expected_files) - set(residue_files))
            )
            modules.append(
                domain.RecipeBenchModule(
                    module_name=candidate_module,
                    actual_files=tuple(sorted(actual_files)),
                    expected_files=expected_files,
                    residue_files=residue_files,
                    slot_growth_files=slot_growth_files,
                    missing_files=missing_files,
                    file_contents=module_file_contents(module_path, actual_files)
                    if candidate_module == selected_module
                    else (),
                )
            )

        modules = list(
            bench_modules_with_content_weights(
                architecture_root=subject_root,
                modules=tuple(modules),
            )
        )
        selected = next(
            (
                bench_module
                for bench_module in modules
                if bench_module.module_name == selected_module
            ),
            domain.RecipeBenchModule(module_name=""),
        )
        recurrence = bench_recurrence_for(modules, signal="residue")
        slot_growth_recurrence = bench_recurrence_for(modules, signal="slot_growth")
        content_weight_recurrence = bench_recurrence_for(
            modules,
            signal="content_weight",
        )
        classification = bench_classification(
            selected=selected,
            modules=tuple(modules),
            recurrence=recurrence,
            slot_growth_recurrence=slot_growth_recurrence,
            content_weight_recurrence=content_weight_recurrence,
        )
        return domain.RecipeBenchReport(
            project_root=project_root,
            recipe_root=self._workspace.recipe_root(),
            architecture_root=subject_root,
            selected_module=selected_module,
            role_name=role_name,
            classification=classification,
            same_role_modules=tuple(modules),
            recurrence=recurrence,
            slot_growth_recurrence=slot_growth_recurrence,
            content_weight_recurrence=content_weight_recurrence,
            selected=selected,
            violations=tuple(violations),
        )

    def build_workspace_report(self) -> domain.RecipeBenchAllReport:
        project_root = self._workspace.project_root()
        try:
            subject_root = self._workspace.subject_root()
        except RuntimeError as exc:
            return domain.RecipeBenchAllReport(
                project_root=project_root,
                recipe_root=self._workspace.recipe_root(),
                architecture_root=Path(),
                classification="local",
                violations=(
                    domain.RecipeCheckViolation(
                        code="config_error",
                        message=str(exc),
                    ),
                ),
            )

        reports = tuple(
            self.build_module_report(module_name)
            for module_name in sorted(self._workspace.config().roles_map)
        )
        violations = tuple(
            violation
            for report in reports
            for violation in report.violations
        )
        return domain.RecipeBenchAllReport(
            project_root=project_root,
            recipe_root=self._workspace.recipe_root(),
            architecture_root=subject_root,
            classification=bench_all_classification(reports),
            reports=reports,
            violations=violations,
        )

def empty_bench_report(
    *,
    project_root: Path,
    recipe_root: Path,
    selected_module: str,
    architecture_root: Path,
    role_name: str,
    violation: domain.RecipeCheckViolation,
) -> domain.RecipeBenchReport:
    return domain.RecipeBenchReport(
        project_root=project_root,
        recipe_root=recipe_root,
        architecture_root=architecture_root,
        selected_module=selected_module,
        role_name=role_name,
        classification="local",
        violations=(violation,),
    )
__all__ = [
    "RecipeBenchService",
    "bench_all_classification",
    "bench_classification",
    "bench_modules_with_content_weights",
    "bench_recurrence_for",
    "module_file_contents",
    "reports_by_role",
]
