from __future__ import annotations

import html
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from enclosure.shared.config import settings
from enclosure.shared.scaffolding import (
    RenderedScaffoldFile,
    Scaffold,
    ScaffoldError,
    scaffolding,
)

from . import domain

_BENCH_CONTENT_LIMIT = 12_000


@dataclass(frozen=True)
class _ComposedLadder:
    family: str = ""
    rung: str = ""
    slots: tuple[Any, ...] = ()
    declared: bool = False

    def is_declared(self) -> bool:
        return self.declared


class _RecipeGenerationService:
    def __init__(
        self,
        *,
        recipe_root: Path,
        config: domain.RecipeGenerationConfig,
    ) -> None:
        self._recipe_root = Path(recipe_root)
        self._config = config

    def list_recipes(self) -> tuple[domain.RecipeSummary, ...]:
        return tuple(self._summarize_recipe(recipe) for recipe in self._load_recipes())

    def show_recipe(self, recipe_name: str) -> domain.RecipeSummary | None:
        recipe = self._load_recipe(recipe_name)
        if recipe is None:
            return None
        return self._summarize_recipe(recipe)

    def check(
        self,
        project_root: Path,
        recipe_name: str | None,
        target_path: Path | str | None,
        *,
        variables: Mapping[str, str],
    ) -> domain.RecipeCheckReport:
        project_root = Path(project_root).resolve()
        violations: list[domain.RecipeCheckViolation] = []

        try:
            recipes = self._load_recipes()
        except ScaffoldError as exc:
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._recipe_root,
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
            recipes_by_name = _recipes_by_name(recipes)
            _validate_recipe_catalog(violations, recipes, recipes_by_name)
            _validate_config_roles_map(
                violations,
                roles_map=self._config.roles_map,
                recipes_by_name=recipes_by_name,
            )
            for recipe in recipes:
                rendered_paths_checked += self._check_recipe(
                    violations,
                    recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=Path("_enclosure_recipe_check") / recipe.name,
                    variables=_check_variables_for(recipe, variables),
                )
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._recipe_root,
                recipes_discovered=len(recipes),
                recipes_checked=len(recipes),
                rendered_paths_checked=rendered_paths_checked,
                violations=tuple(violations),
            )

        recipe = self._load_recipe(recipe_name)
        if recipe is None:
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._recipe_root,
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

        recipes_by_name = _recipes_by_name(recipes)
        _validate_recipe_catalog(violations, recipes, recipes_by_name)
        _validate_config_roles_map(
            violations,
            roles_map=self._config.roles_map,
            recipes_by_name=recipes_by_name,
        )
        rendered_paths_checked = self._check_recipe(
            violations,
            recipe,
            recipes_by_name=recipes_by_name,
            project_root=project_root,
            target_path=target_path or Path("_enclosure_recipe_check") / recipe.name,
            variables=_check_variables_for(recipe, variables),
        )

        return domain.RecipeCheckReport(
            project_root=project_root,
            recipe_root=self._recipe_root,
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
            rendered_files = self._render_files(
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
        if (
            recipe.role in {"archetype", "fragment"}
            and not recipe.ladder.is_declared()
        ):
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

    def describe(
        self,
        recipe_name: str,
        project_root: Path,
        target_path: Path | str,
        *,
        variables: Mapping[str, str],
    ) -> domain.RecipeGenerationReport:
        project_root = Path(project_root).resolve()
        recipe = self._load_recipe(recipe_name)
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
        recipes_by_name = _recipes_by_name(self._load_recipes())

        rendered_files = self._render_files(
            recipe,
            recipes_by_name=recipes_by_name,
            project_root=project_root,
            target_path=target_path,
            variables=variables,
        )
        preview_files = self._plan_preview_files(rendered_files)
        create_paths, skipped_paths = _paths_from_preview_files(preview_files)
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
        project_root: Path,
        target_path: Path | str,
        *,
        variables: Mapping[str, str],
    ) -> domain.GenerateRecipeResult:
        project_root = Path(project_root).resolve()
        recipe = self._load_recipe(recipe_name)
        if recipe is None:
            return {
                "recipe_name": recipe_name,
                "project_root": project_root,
                "recipe_found": False,
                "recipe_empty": False,
                "created_paths": (),
                "skipped_paths": (),
            }
        recipes_by_name = _recipes_by_name(self._load_recipes())

        rendered_files = self._render_files(
            recipe,
            recipes_by_name=recipes_by_name,
            project_root=project_root,
            target_path=target_path,
            variables=variables,
        )
        create_paths, skipped_paths = self._plan_paths(rendered_files)
        scaffolding.write(rendered_files, create_paths=create_paths)

        return {
            "recipe_name": recipe.name,
            "project_root": project_root,
            "recipe_found": True,
            "recipe_empty": recipe.is_empty(),
            "created_paths": create_paths,
            "skipped_paths": skipped_paths,
        }

    def _load_recipes(self) -> tuple[Scaffold, ...]:
        return scaffolding.load_all(self._recipe_root)

    def _load_recipe(self, recipe_name: str) -> Scaffold | None:
        try:
            return scaffolding.load(self._recipe_root, recipe_name)
        except LookupError:
            return None

    def _render_files(
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

    def _plan_paths(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
    ) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
        return _paths_from_preview_files(self._plan_preview_files(rendered_files))

    def _plan_preview_files(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
    ) -> tuple[domain.RecipePreviewFile, ...]:
        preview_files: list[domain.RecipePreviewFile] = []
        for rendered_file in rendered_files:
            target_path = rendered_file.target_path
            relative_path = rendered_file.relative_path
            if self._config.should_skip(relative_path):
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

    def drifts(self, project_root: Path) -> domain.RecipeDriftReport:
        project_root = Path(project_root).resolve()
        violations: list[domain.RecipeCheckViolation] = []
        try:
            recipes = self._load_recipes()
        except ScaffoldError as exc:
            return domain.RecipeDriftReport(
                project_root=project_root,
                recipe_root=self._recipe_root,
                architecture_root=Path(),
                modules_checked=0,
                violations=(
                    domain.RecipeCheckViolation(
                        code="invalid_manifest",
                        message=str(exc),
                    ),
                ),
            )

        recipes_by_name = _recipes_by_name(recipes)
        _validate_recipe_catalog(violations, recipes, recipes_by_name)
        architecture_root = _architecture_root(project_root)
        roles_map = self._config.roles_map
        _validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )
        drifts: list[domain.RecipeDrift] = []
        for module_name, role_name in sorted(roles_map.items()):
            role_recipe = _recipe_for_role(role_name, recipes_by_name)
            module_path = architecture_root / module_name
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
                expected_files = _expected_files_for(
                    self,
                    role_recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=architecture_root.relative_to(project_root) / module_name,
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

            actual_files = _actual_files_for(
                module_path,
                project_root=project_root,
                config=self._config,
            )
            ladder = _composed_ladder_for(role_recipe, recipes_by_name)
            missing_files, extra_files = _drift_files_for(
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

        for module_name in _actual_module_names(
            architecture_root,
            project_root=project_root,
            config=self._config,
        ):
            if module_name not in roles_map:
                drifts.append(
                    domain.RecipeDrift(
                        module_name=module_name,
                        role_name="",
                        extra_files=_actual_files_for(
                            architecture_root / module_name,
                            project_root=project_root,
                            config=self._config,
                        ),
                    )
                )

        return domain.RecipeDriftReport(
            project_root=project_root,
            recipe_root=self._recipe_root,
            architecture_root=architecture_root,
            modules_checked=len(drifts),
            drifts=tuple(drifts),
            violations=tuple(violations),
        )

    def bench(self, project_root: Path, module_name: str) -> domain.RecipeBenchReport:
        project_root = Path(project_root).resolve()
        selected_module = module_name.strip().replace("\\", "/")
        violations: list[domain.RecipeCheckViolation] = []
        try:
            recipes = self._load_recipes()
        except ScaffoldError as exc:
            return _empty_bench_report(
                project_root=project_root,
                recipe_root=self._recipe_root,
                selected_module=selected_module,
                violation=domain.RecipeCheckViolation(
                    code="invalid_manifest",
                    message=str(exc),
                ),
            )

        recipes_by_name = _recipes_by_name(recipes)
        _validate_recipe_catalog(violations, recipes, recipes_by_name)
        roles_map = self._config.roles_map
        _validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )

        architecture_root = _architecture_root(project_root)
        role_name = roles_map.get(selected_module, "")
        if not role_name:
            return _empty_bench_report(
                project_root=project_root,
                recipe_root=self._recipe_root,
                architecture_root=architecture_root,
                selected_module=selected_module,
                violation=domain.RecipeCheckViolation(
                    code="module_unmapped",
                    message=(
                        "Module is not mapped in workspace.recipe.roles_map: "
                        f"{selected_module}"
                    ),
                    recipe_name="workspace.recipe.roles_map",
                ),
            )

        role_recipe = _recipe_for_role(role_name, recipes_by_name)
        if role_recipe is None:
            return _empty_bench_report(
                project_root=project_root,
                recipe_root=self._recipe_root,
                architecture_root=architecture_root,
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

        selected_path = architecture_root / selected_module
        if not selected_path.is_dir():
            return _empty_bench_report(
                project_root=project_root,
                recipe_root=self._recipe_root,
                architecture_root=architecture_root,
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
            module_path = architecture_root / candidate_module
            if not module_path.is_dir():
                violations.append(
                    domain.RecipeCheckViolation(
                        code="mapped_module_missing",
                        message=f"Mapped module does not exist: {candidate_module}",
                        recipe_name="workspace.recipe.roles_map",
                    )
                )
                continue

            target_path = architecture_root.relative_to(project_root) / candidate_module
            try:
                rendered_files = self._render_files(
                    role_recipe,
                    recipes_by_name=recipes_by_name,
                    project_root=project_root,
                    target_path=target_path,
                    variables=_sample_variables_for_rendering(
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

            expected_files = _module_relative_rendered_paths(
                rendered_files,
                target_path=target_path,
            )
            actual_files = _actual_files_for(
                module_path,
                project_root=project_root,
                config=self._config,
            )
            missing_files, residue_files = _drift_files_for(
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
                    file_contents=_module_file_contents(module_path, actual_files)
                    if candidate_module == selected_module
                    else (),
                )
            )

        modules = list(
            _bench_modules_with_content_weights(
                architecture_root=architecture_root,
                modules=tuple(modules),
            )
        )
        selected = next(
            (
                bench_module
                for bench_module in modules
                if bench_module.module_name == selected_module
            ),
            None,
        )
        recurrence = _bench_recurrence_for(modules, signal="residue")
        slot_growth_recurrence = _bench_recurrence_for(modules, signal="slot_growth")
        content_weight_recurrence = _bench_recurrence_for(
            modules,
            signal="content_weight",
        )
        classification = _bench_classification(
            selected=selected,
            modules=tuple(modules),
            recurrence=recurrence,
            slot_growth_recurrence=slot_growth_recurrence,
            content_weight_recurrence=content_weight_recurrence,
        )
        return domain.RecipeBenchReport(
            project_root=project_root,
            recipe_root=self._recipe_root,
            architecture_root=architecture_root,
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

    def bench_all(self, project_root: Path) -> domain.RecipeBenchAllReport:
        project_root = Path(project_root).resolve()
        try:
            architecture_root = _architecture_root(project_root)
        except RuntimeError as exc:
            return domain.RecipeBenchAllReport(
                project_root=project_root,
                recipe_root=self._recipe_root,
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
            self.bench(project_root, module_name)
            for module_name in sorted(self._config.roles_map)
        )
        violations = tuple(
            violation
            for report in reports
            for violation in report.violations
        )
        return domain.RecipeBenchAllReport(
            project_root=project_root,
            recipe_root=self._recipe_root,
            architecture_root=architecture_root,
            classification=_bench_all_classification(reports),
            reports=reports,
            violations=violations,
        )

    def _summarize_recipe(self, recipe: Scaffold) -> domain.RecipeSummary:
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


def generate_recipe(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.GenerateRecipeResult:
    project_root = settings.metadata.project_root
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).generate(recipe_name, project_root, target_path, variables=variables)


def recipe_command_context() -> domain.RecipeCommandContext:
    return domain.RecipeCommandContext(
        project_root=settings.metadata.project_root,
        recipe_root=settings.metadata.recipes_dir,
    )


def describe_recipe_generation(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.RecipeGenerationReport:
    project_root = settings.metadata.project_root
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).describe(recipe_name, project_root, target_path, variables=variables)


def list_recipes(
    *,
    recipe_root: Path,
) -> tuple[domain.RecipeSummary, ...]:
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=domain.RecipeGenerationConfig(skip=()),
    ).list_recipes()


def show_recipe(
    recipe_name: str,
    *,
    recipe_root: Path,
) -> domain.RecipeSummary | None:
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=domain.RecipeGenerationConfig(skip=()),
    ).show_recipe(recipe_name)


def check_recipes(
    *,
    recipe_root: Path,
    recipe_name: str | None,
    target_path: Path | str | None,
    variables: Mapping[str, str],
) -> domain.RecipeCheckReport:
    project_root = settings.metadata.project_root
    recipe_settings = _load_recipe_generation_settings()
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=domain.RecipeGenerationConfig(
            skip=(),
            roles_map=recipe_settings.roles_map,
        ),
    ).check(
        project_root,
        recipe_name,
        target_path,
        variables=variables,
    )


def check_recipe_drifts(
    *,
    recipe_root: Path,
) -> domain.RecipeDriftReport:
    project_root = settings.metadata.project_root
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).drifts(project_root)


def bench_preview(
    module_name: str,
    *,
    recipe_root: Path,
) -> domain.RecipeBenchReport:
    project_root = settings.metadata.project_root
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).bench(project_root, module_name)


def bench_all_preview(
    *,
    recipe_root: Path,
) -> domain.RecipeBenchAllReport:
    project_root = settings.metadata.project_root
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).bench_all(project_root)


def render_recipe_bench_html(report: domain.RecipeBenchReport) -> str:
    return _render_bench_html(report)


def render_recipe_bench_all_html(report: domain.RecipeBenchAllReport) -> str:
    return _render_bench_all_html(report)


def _load_recipe_generation_settings() -> domain.RecipeGenerationConfig:
    recipe_settings = settings.query("workspace.recipe")
    if not isinstance(recipe_settings, domain.RecipeGenerationConfig):
        raise RuntimeError("workspace.recipe settings were not validated")
    return recipe_settings


def _check_variables_for(
    recipe: Scaffold,
    variables: Mapping[str, str],
) -> dict[str, str]:
    check_variables = dict(variables)
    for input_spec in recipe.inputs:
        if input_spec.name in check_variables:
            continue
        if not input_spec.required:
            continue
        check_variables[input_spec.name] = _sample_value_for(input_spec)
    return check_variables


def _sample_variables_for_rendering(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> dict[str, str]:
    variables: dict[str, str] = {}
    for input_spec in _composed_recipe_inputs(recipe, recipes_by_name):
        if not input_spec.required or input_spec.name in variables:
            continue
        variables[input_spec.name] = _sample_value_for(input_spec)
    return variables


def _sample_value_for(input_spec: Any) -> str:
    if input_spec.choices:
        return input_spec.choices[0]
    if input_spec.value_type == "list":
        return "sample"
    if input_spec.value_type == "path":
        return "sample"
    if input_spec.value_type == "dotted_name":
        return "sample"
    return "sample"


def _paths_from_preview_files(
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


def _recipes_by_name(recipes: tuple[Scaffold, ...]) -> dict[str, Scaffold]:
    return {recipe.name: recipe for recipe in recipes}


def _recipe_for_role(
    role_name: str,
    recipes_by_name: Mapping[str, Scaffold],
) -> Scaffold | None:
    if "+" not in role_name:
        return recipes_by_name.get(role_name)

    include_names = tuple(part.strip() for part in role_name.split("+") if part.strip())
    if not include_names:
        return None
    if any(include_name not in recipes_by_name for include_name in include_names):
        return None
    if any(
        recipes_by_name[include_name].role == "container"
        for include_name in include_names
    ):
        return None
    return Scaffold(
        name="composed-role",
        source_root=Path("."),
        role="archetype",
        description="Composed recipe role",
        ladder=_ComposedLadder(
            family="composed",
            rung=role_name,
            declared=True,
        ),
        includes=include_names,
    )


def _composed_recipe_inputs(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> tuple[Any, ...]:
    composed_recipes = scaffolding.compose(recipe, tuple(recipes_by_name.values()))
    return tuple(input_spec for scaffold in composed_recipes for input_spec in scaffold.inputs)


def _composed_ladder_for(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> Any:
    slots_by_name: dict[str, Any] = {}
    for composed_recipe in scaffolding.compose(recipe, tuple(recipes_by_name.values())):
        for slot in composed_recipe.ladder.slots:
            slots_by_name[_slot_name(slot)] = slot
    return _ComposedLadder(
        family=recipe.ladder.family,
        rung=recipe.ladder.rung,
        slots=tuple(slots_by_name.values()),
        declared=recipe.ladder.is_declared(),
    )


def _slot_name(slot: Any) -> str:
    name = slot.name
    return name.value if hasattr(name, "value") else str(name)


def _slot_state(slot: Any) -> str:
    state = slot.state
    return state.value if hasattr(state, "value") else str(state)


def _relative_path_text(path: Path | str) -> str:
    return Path(path).as_posix().strip("/")


def _validate_recipe_catalog(
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


def _validate_config_roles_map(
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
        role_recipe = _recipe_for_role(role_name, recipes_by_name)
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


def _architecture_root(project_root: Path) -> Path:
    return settings.architecture_root()


def _expected_files_for(
    service: _RecipeGenerationService,
    recipe: Scaffold,
    *,
    recipes_by_name: Mapping[str, Scaffold],
    project_root: Path,
    target_path: Path,
) -> set[str]:
    rendered_files = service._render_files(
        recipe,
        recipes_by_name=recipes_by_name,
        project_root=project_root,
        target_path=target_path,
        variables=_sample_variables_for_rendering(recipe, recipes_by_name),
    )
    return set(_module_relative_rendered_paths(rendered_files, target_path=target_path))


def _module_relative_rendered_paths(
    rendered_files: tuple[RenderedScaffoldFile, ...],
    *,
    target_path: Path | str,
) -> tuple[str, ...]:
    prefix = _relative_path_text(target_path) + "/"
    return tuple(
        sorted(
            rendered_file.relative_path.as_posix().removeprefix(prefix)
            for rendered_file in rendered_files
        )
    )


def _bench_recurrence_for(
    modules: tuple[domain.RecipeBenchModule, ...] | list[domain.RecipeBenchModule],
    *,
    signal: str,
) -> tuple[domain.RecipeBenchRecurrence, ...]:
    modules_by_path: dict[str, list[str]] = {}
    for bench_module in modules:
        for signal_path in _bench_signal_paths(bench_module, signal=signal):
            modules_by_path.setdefault(signal_path, []).append(bench_module.module_name)

    counts = Counter(
        signal_path
        for bench_module in modules
        for signal_path in _bench_signal_paths(bench_module, signal=signal)
    )
    module_count = len(tuple(modules))
    return tuple(
        domain.RecipeBenchRecurrence(
            path=signal_path,
            count=count,
            modules=tuple(sorted(modules_by_path[signal_path])),
            label=_bench_recurrence_label(count, module_count),
        )
        for signal_path, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _bench_signal_paths(
    bench_module: domain.RecipeBenchModule,
    *,
    signal: str,
) -> tuple[str, ...]:
    if signal == "residue":
        return bench_module.residue_files
    if signal == "slot_growth":
        return bench_module.slot_growth_files
    if signal == "content_weight":
        return tuple(weight.path for weight in bench_module.content_weights)
    raise ValueError(f"Unsupported bench signal: {signal}")


def _bench_recurrence_label(count: int, module_count: int) -> str:
    if count <= 1:
        return "local"
    if module_count and count / module_count >= 0.67:
        return "established"
    return "emerging"


def _bench_classification(
    *,
    selected: domain.RecipeBenchModule | None,
    modules: tuple[domain.RecipeBenchModule, ...],
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    slot_growth_recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    content_weight_recurrence: tuple[domain.RecipeBenchRecurrence, ...],
) -> str:
    if selected is None or not selected.has_warp():
        return "clean"

    selected_recurrence = (
        _selected_recurrence_for(selected.residue_files, recurrence)
        + _selected_recurrence_for(
            selected.slot_growth_files,
            slot_growth_recurrence,
        )
        + _selected_recurrence_for(
            tuple(weight.path for weight in selected.content_weights),
            content_weight_recurrence,
        )
    )
    if _same_role_warp_is_unstable(modules):
        return "unstable"
    if any(item.label == "established" for item in selected_recurrence):
        return "established"
    if any(item.count > 1 for item in selected_recurrence):
        return "emerging"
    return "local"


def _selected_recurrence_for(
    paths: tuple[str, ...],
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
) -> tuple[domain.RecipeBenchRecurrence, ...]:
    recurrence_by_path = {item.path: item for item in recurrence}
    return tuple(
        recurrence_by_path[path]
        for path in paths
        if path in recurrence_by_path
    )


def _same_role_warp_is_unstable(
    modules: tuple[domain.RecipeBenchModule, ...],
) -> bool:
    warped_modules = tuple(module for module in modules if module.has_warp())
    if len(warped_modules) <= 1:
        return False

    fingerprints = {
        _bench_module_warp_fingerprint(module)
        for module in warped_modules
    }
    if len(fingerprints) <= 1:
        return False

    common_paths = set(_bench_module_warp_paths(warped_modules[0]))
    for module in warped_modules[1:]:
        common_paths &= set(_bench_module_warp_paths(module))
    return not common_paths


def _bench_module_warp_fingerprint(
    module: domain.RecipeBenchModule,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            (
                *(f"missing:{path}" for path in module.missing_files),
                *(f"residue:{path}" for path in module.residue_files),
                *(f"slot:{path}" for path in module.slot_growth_files),
                *(f"weight:{weight.path}" for weight in module.content_weights),
            )
        )
    )


def _bench_module_warp_paths(module: domain.RecipeBenchModule) -> tuple[str, ...]:
    return tuple(
        sorted(
            (
                *module.missing_files,
                *module.residue_files,
                *module.slot_growth_files,
                *(weight.path for weight in module.content_weights),
            )
        )
    )


def _bench_all_classification(
    reports: tuple[domain.RecipeBenchReport, ...],
) -> str:
    if not any(report.local_warp_count for report in reports):
        return "clean"
    classifications = {report.classification for report in reports}
    if "unstable" in classifications:
        return "unstable"
    if "established" in classifications:
        return "established"
    if "emerging" in classifications:
        return "emerging"
    return "local"


def _reports_by_role(
    reports: tuple[domain.RecipeBenchReport, ...],
) -> dict[str, tuple[domain.RecipeBenchReport, ...]]:
    reports_by_role: dict[str, list[domain.RecipeBenchReport]] = {}
    for report in reports:
        reports_by_role.setdefault(report.role_name or "unknown", []).append(report)
    return {
        role_name: tuple(role_reports)
        for role_name, role_reports in sorted(reports_by_role.items())
    }


def _empty_bench_report(
    *,
    project_root: Path,
    recipe_root: Path,
    selected_module: str,
    architecture_root: Path = Path(),
    role_name: str = "",
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


def _bench_modules_with_content_weights(
    *,
    architecture_root: Path,
    modules: tuple[domain.RecipeBenchModule, ...],
) -> tuple[domain.RecipeBenchModule, ...]:
    metrics_by_module: dict[str, dict[str, tuple[int, int]]] = {}
    metrics_by_path: dict[str, list[tuple[int, int]]] = {}
    for module in modules:
        module_metrics: dict[str, tuple[int, int]] = {}
        module_path = architecture_root / module.module_name
        for relative_path in module.actual_files:
            metrics = _content_metrics_for(module_path / relative_path)
            if metrics is None:
                continue
            module_metrics[relative_path] = metrics
            metrics_by_path.setdefault(relative_path, []).append(metrics)
        metrics_by_module[module.module_name] = module_metrics

    weighted_modules: list[domain.RecipeBenchModule] = []
    for module in modules:
        weights: list[domain.RecipeBenchContentWeight] = []
        for relative_path, metrics in metrics_by_module[module.module_name].items():
            reason = _content_weight_reason(
                metrics,
                baseline_metrics=tuple(metrics_by_path.get(relative_path, ())),
            )
            if not reason:
                continue
            line_count, symbol_count = metrics
            weights.append(
                domain.RecipeBenchContentWeight(
                    path=relative_path,
                    line_count=line_count,
                    symbol_count=symbol_count,
                    reason=reason,
                )
            )
        weighted_modules.append(
            replace(
                module,
                content_weights=tuple(sorted(weights, key=lambda weight: weight.path)),
            )
        )
    return tuple(weighted_modules)


def _content_metrics_for(path: Path) -> tuple[int, int] | None:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    return len(content.splitlines()), 0


def _content_weight_reason(
    metrics: tuple[int, int],
    *,
    baseline_metrics: tuple[tuple[int, int], ...],
) -> str:
    line_count, symbol_count = metrics
    reasons: list[str] = []
    if line_count >= 300:
        reasons.append(f"{line_count} lines")
    if symbol_count >= 20:
        reasons.append(f"{symbol_count} symbols")

    if len(baseline_metrics) > 1:
        median_lines = _median(tuple(item[0] for item in baseline_metrics))
        median_symbols = _median(tuple(item[1] for item in baseline_metrics))
        if median_lines and line_count >= 80 and line_count >= median_lines * 2:
            reasons.append(f"{line_count} lines vs median {median_lines}")
        if median_symbols and symbol_count >= 8 and symbol_count >= median_symbols * 2:
            reasons.append(f"{symbol_count} symbols vs median {median_symbols}")

    return "; ".join(dict.fromkeys(reasons))


def _median(values: tuple[int, ...]) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) // 2


def _module_file_contents(
    module_path: Path,
    actual_files: set[str],
) -> tuple[domain.RecipeBenchFileContent, ...]:
    contents: list[domain.RecipeBenchFileContent] = []
    for relative_path in sorted(actual_files):
        path = module_path / relative_path
        try:
            content = path.read_text(encoding="utf-8")
            truncated = len(content) > _BENCH_CONTENT_LIMIT
            if truncated:
                content = content[:_BENCH_CONTENT_LIMIT]
        except UnicodeDecodeError:
            content = "[binary or non-UTF-8 file]"
            truncated = False
        contents.append(
            domain.RecipeBenchFileContent(
                path=relative_path,
                content=content,
                truncated=truncated,
            )
        )
    return tuple(contents)


def _drift_files_for(
    recipe: Scaffold,
    *,
    recipes_by_name: Mapping[str, Scaffold],
    expected_files: set[str],
    actual_files: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ladder = _composed_ladder_for(recipe, recipes_by_name)
    if not ladder.is_declared():
        return (
            tuple(sorted(expected_files - actual_files)),
            tuple(sorted(actual_files - expected_files)),
        )

    required_files = set(expected_files)
    allowed_files = set(expected_files)
    allowed_prefixes: set[str] = set()
    forbidden_file_stems: set[str] = set()
    forbidden_prefixes: set[str] = set()

    for slot in ladder.slots:
        slot_path = _slot_name(slot)
        slot_state = _slot_state(slot)
        if slot_state == "absent":
            forbidden_file_stems.add(slot_path)
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot_state == "file":
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot_state == "package":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            continue

        if slot_state == "split-files":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            for slot_file in slot.files:
                slot_file_path = f"{slot_path}/{slot_file}"
                required_files.add(slot_file_path)
                allowed_files.add(slot_file_path)
                if Path(slot_file).suffix:
                    forbidden_prefixes.add(
                        f"{slot_path}/{Path(slot_file).with_suffix('').as_posix()}/"
            )
            continue

        if slot_state == "split-packages":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            for slot_package in slot.packages:
                slot_package_path = f"{slot_path}/{slot_package}"
                allowed_prefixes.add(f"{slot_package_path}/")
                forbidden_file_stems.add(slot_package_path)

    missing_files = tuple(sorted(required_files - actual_files))
    extra_files = tuple(
        sorted(
            actual_file
            for actual_file in actual_files
            if _is_extra_ladder_file(
                actual_file,
                allowed_files=allowed_files,
                allowed_prefixes=allowed_prefixes,
                forbidden_file_stems=forbidden_file_stems,
                forbidden_prefixes=forbidden_prefixes,
            )
        )
    )
    return missing_files, extra_files


def _is_extra_ladder_file(
    actual_file: str,
    *,
    allowed_files: set[str],
    allowed_prefixes: set[str],
    forbidden_file_stems: set[str],
    forbidden_prefixes: set[str],
) -> bool:
    if _matches_file_stem(actual_file, forbidden_file_stems):
        return True
    if any(actual_file.startswith(prefix) for prefix in forbidden_prefixes):
        return True
    if actual_file in allowed_files:
        return False
    return not any(actual_file.startswith(prefix) for prefix in allowed_prefixes)


def _matches_file_stem(actual_file: str, forbidden_file_stems: set[str]) -> bool:
    if not forbidden_file_stems:
        return False
    actual_path = Path(actual_file)
    if not actual_path.suffix:
        return False
    return actual_path.with_suffix("").as_posix() in forbidden_file_stems


def _actual_files_for(
    module_path: Path,
    *,
    project_root: Path | None = None,
    config: domain.RecipeGenerationConfig | None = None,
) -> set[str]:
    return {
        path.relative_to(module_path).as_posix()
        for path in module_path.rglob("*")
        if path.is_file()
        and not _should_skip_actual_file(
            path,
            module_path=module_path,
            project_root=project_root,
            config=config,
        )
    }


def _should_skip_actual_file(
    path: Path,
    *,
    module_path: Path,
    project_root: Path | None,
    config: domain.RecipeGenerationConfig | None,
) -> bool:
    if config is None:
        return False

    relative_candidates = [
        path.relative_to(module_path),
    ]
    if project_root is not None:
        relative_candidates.append(path.relative_to(project_root))

    return any(
        config.should_skip(relative_path)
        for relative_path in relative_candidates
    )


def _actual_module_names(
    architecture_root: Path,
    *,
    project_root: Path,
    config: domain.RecipeGenerationConfig,
) -> tuple[str, ...]:
    return tuple(
        module_path.relative_to(architecture_root).as_posix()
        for module_path in sorted(architecture_root.glob("*/*"))
        if module_path.is_dir()
        and _actual_files_for(
            module_path,
            project_root=project_root,
            config=config,
        )
    )


def _render_bench_all_html(report: domain.RecipeBenchAllReport) -> str:
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Workspace Warp Index</title>",
            f"<style>{_bench_css()}</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<p class=\"eyebrow\">Workspace Warp Index</p>",
            "<h1>All Mapped Modules</h1>",
            _bench_all_summary_grid(report),
            "</header>",
            _bench_all_violations_section(report),
            _bench_all_worst_modules_section(report),
            _bench_all_roles_section(report),
            _interpretation_section(),
            "</main>",
            "</body>",
            "</html>",
        )
    )


def _bench_all_summary_grid(report: domain.RecipeBenchAllReport) -> str:
    cells = (
        ("Modules", str(report.module_count), ""),
        ("Roles", str(report.role_count), ""),
        ("Modules with warp", str(report.reports_with_warp_count), _count_severity(report.reports_with_warp_count)),
        ("Forbidden residue", str(report.local_residue_count), _count_severity(report.local_residue_count)),
        ("Slot growth", str(report.local_slot_growth_count), _count_severity(report.local_slot_growth_count)),
        ("Content weight", str(report.local_content_weight_count), _count_severity(report.local_content_weight_count)),
        ("Classification", report.classification, _classification_severity(report.classification)),
    )
    return "<section class=\"summary\">" + "".join(
        f"<div class=\"{_escape(_summary_class(severity))}\">"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
        for label, value, severity in cells
    ) + "</section>"


def _bench_all_violations_section(report: domain.RecipeBenchAllReport) -> str:
    if not report.violations:
        return ""
    items = "".join(
        "<li>"
        f"<code>{_escape(violation.code)}</code> "
        f"{_escape(violation.message)}"
        "</li>"
        for violation in report.violations
    )
    return f"<section><h2>Blocking Findings</h2><ul>{items}</ul></section>"


def _bench_all_worst_modules_section(report: domain.RecipeBenchAllReport) -> str:
    ranked_reports = tuple(
        sorted(
            report.reports,
            key=lambda item: (
                -item.local_warp_count,
                -item.repeated_warp_count,
                item.selected_module,
            ),
        )
    )
    if not ranked_reports:
        return "<section><h2>Module Index</h2><p>No mapped modules.</p></section>"
    rows = "".join(_bench_all_module_row(item) for item in ranked_reports)
    return (
        "<section><h2>Module Index</h2>"
        "<div class=\"table-wrap\"><table>"
        "<thead><tr>"
        "<th>Module</th><th>Role</th><th>Expected</th><th>Actual</th>"
        "<th>Warp</th><th>Residue</th><th>Slot Growth</th><th>Content</th>"
        "<th>Repeated</th><th>Classification</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
        "</section>"
    )


def _bench_all_module_row(report: domain.RecipeBenchReport) -> str:
    selected = report.selected
    expected_count = len(selected.expected_files) if selected is not None else 0
    actual_count = len(selected.actual_files) if selected is not None else 0
    severity = _classification_severity(report.classification)
    return (
        f"<tr class=\"{_escape(_row_class(severity))}\">"
        f"<th><code>{_escape(report.selected_module)}</code></th>"
        f"<td>{_escape(report.role_name or 'unknown')}</td>"
        f"<td>{expected_count}</td>"
        f"<td>{actual_count}</td>"
        f"{_count_cell(report.local_warp_count)}"
        f"{_count_cell(report.local_residue_count)}"
        f"{_count_cell(report.local_slot_growth_count)}"
        f"{_count_cell(report.local_content_weight_count)}"
        f"{_count_cell(report.repeated_warp_count)}"
        f"<td>{_badge(report.classification, severity)}</td>"
        "</tr>"
    )


def _bench_all_roles_section(report: domain.RecipeBenchAllReport) -> str:
    role_sections = "".join(
        _bench_all_role_section(role_name, role_reports)
        for role_name, role_reports in _reports_by_role(report.reports).items()
    )
    if not role_sections:
        role_sections = "<p>No roles to compare.</p>"
    return f"<section><h2>Roles</h2>{role_sections}</section>"


def _bench_all_role_section(
    role_name: str,
    reports: tuple[domain.RecipeBenchReport, ...],
) -> str:
    residue_total = sum(item.local_residue_count for item in reports)
    slot_growth_total = sum(item.local_slot_growth_count for item in reports)
    content_weight_total = sum(item.local_content_weight_count for item in reports)
    repeated_total = sum(item.repeated_warp_count for item in reports)
    recurrence = reports[0].recurrence if reports else ()
    slot_growth_recurrence = reports[0].slot_growth_recurrence if reports else ()
    content_weight_recurrence = reports[0].content_weight_recurrence if reports else ()
    return (
        "<article class=\"role-block\">"
        f"<h3>{_escape(role_name)}</h3>"
        "<p>"
        f"{len(reports)} module(s), {residue_total} residue, "
        f"{slot_growth_total} slot growth, {content_weight_total} content weight, "
        f"{repeated_total} repeated signal(s)."
        "</p>"
        f"{_role_module_table(reports)}"
        f"{_role_recurrence_bars('Forbidden residue', recurrence, len(reports))}"
        f"{_role_recurrence_bars('Slot growth', slot_growth_recurrence, len(reports))}"
        f"{_role_recurrence_bars('Content weight', content_weight_recurrence, len(reports))}"
        "</article>"
    )


def _role_module_table(reports: tuple[domain.RecipeBenchReport, ...]) -> str:
    rows = "".join(
        f"<tr class=\"{_escape(_row_class(_classification_severity(report.classification)))}\">"
        f"<th><code>{_escape(report.selected_module)}</code></th>"
        f"{_count_cell(report.local_warp_count)}"
        f"{_count_cell(report.local_residue_count)}"
        f"{_count_cell(report.local_slot_growth_count)}"
        f"{_count_cell(report.local_content_weight_count)}"
        f"{_count_cell(report.repeated_warp_count)}"
        f"<td>{_badge(report.classification, _classification_severity(report.classification))}</td>"
        "</tr>"
        for report in reports
    )
    return (
        "<div class=\"table-wrap\"><table>"
        "<thead><tr><th>Module</th><th>Warp</th><th>Residue</th>"
        "<th>Slot Growth</th><th>Content</th><th>Repeated</th>"
        "<th>Classification</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )


def _role_recurrence_bars(
    title: str,
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    module_count: int,
) -> str:
    if not recurrence:
        return f"<p class=\"empty\">No {_escape(title.lower())} recurrence.</p>"
    total = max(module_count, 1)
    return f"<h4>{_escape(title)}</h4><div class=\"role-bars\">" + "".join(
        f"<div class=\"bar-row { _escape(_row_class(_classification_severity(item.label))) }\">"
        f"<code>{_escape(item.path)}</code>"
        "<div class=\"bar-track\">"
        f"<span class=\"{_escape(_bar_class(_classification_severity(item.label)))}\" style=\"width: {int((item.count / total) * 100)}%\"></span>"
        "</div>"
        f"<strong>{item.count}/{total} {_badge(item.label, _classification_severity(item.label))}</strong>"
        "</div>"
        for item in recurrence
    ) + "</div>"


def _render_bench_html(report: domain.RecipeBenchReport) -> str:
    selected = report.selected
    residue_paths = tuple(item.path for item in report.recurrence)
    title = f"Bench Preview: {report.selected_module}"
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_escape(title)}</title>",
            f"<style>{_bench_css()}</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<p class=\"eyebrow\">Bench Preview Warp Report</p>",
            f"<h1>{_escape(report.selected_module)}</h1>",
            _summary_grid(report),
            "</header>",
            _violations_section(report),
            _three_column_section(selected),
            _matrix_section(report, residue_paths),
            _recurrence_section(report),
            _interpretation_section(),
            "</main>",
            "</body>",
            "</html>",
        )
    )


def _summary_grid(report: domain.RecipeBenchReport) -> str:
    cells = (
        ("Recipe role", report.role_name or "unknown", ""),
        ("Same-role modules", str(report.same_role_module_count), ""),
        ("Local warp", str(report.local_warp_count), _count_severity(report.local_warp_count)),
        ("Forbidden residue", str(report.local_residue_count), _count_severity(report.local_residue_count)),
        ("Slot growth", str(report.local_slot_growth_count), _count_severity(report.local_slot_growth_count)),
        ("Content weight", str(report.local_content_weight_count), _count_severity(report.local_content_weight_count)),
        ("Repeated warp", str(report.repeated_warp_count), _count_severity(report.repeated_warp_count)),
        ("Classification", report.classification, _classification_severity(report.classification)),
    )
    return "<section class=\"summary\">" + "".join(
        f"<div class=\"{_escape(_summary_class(severity))}\">"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
        for label, value, severity in cells
    ) + "</section>"


def _violations_section(report: domain.RecipeBenchReport) -> str:
    if not report.violations:
        return ""
    items = "".join(
        "<li>"
        f"<code>{_escape(violation.code)}</code> "
        f"{_escape(violation.message)}"
        "</li>"
        for violation in report.violations
    )
    return f"<section><h2>Blocking Findings</h2><ul>{items}</ul></section>"


def _three_column_section(selected: domain.RecipeBenchModule | None) -> str:
    if selected is None:
        return (
            "<section><h2>Module Bench</h2>"
            "<p>No selected module data could be collected.</p></section>"
        )
    return (
        "<section><h2>Module Bench</h2>"
        "<div class=\"columns\">"
        f"<article><h3>Actual Tree</h3>{_tree(selected.actual_files)}"
        f"{_file_content_details(selected.file_contents)}</article>"
        f"<article><h3>Recipe Expected</h3>{_tree(selected.expected_files)}</article>"
        f"<article><h3>Missing Expected</h3>{_tree(selected.missing_files)}"
        f"<h3>Forbidden Residue</h3>{_tree(selected.residue_files)}"
        f"<h3>Slot Growth</h3>{_tree(selected.slot_growth_files)}"
        f"<h3>Content Weight</h3>{_content_weight_list(selected.content_weights)}</article>"
        "</div>"
        "</section>"
    )


def _tree(paths: tuple[str, ...]) -> str:
    if not paths:
        return "<p class=\"empty\">No files.</p>"
    return "<ul class=\"tree\">" + "".join(
        f"<li><code>{_escape(path)}</code></li>"
        for path in paths
    ) + "</ul>"


def _file_content_details(
    files: tuple[domain.RecipeBenchFileContent, ...],
) -> str:
    if not files:
        return ""
    return "<div class=\"contents\">" + "".join(
        "<details>"
        f"<summary>{_escape(file.path)}"
        f"{' (truncated)' if file.truncated else ''}</summary>"
        f"<pre>{_escape(file.content)}</pre>"
        "</details>"
        for file in files
    ) + "</div>"


def _content_weight_list(
    weights: tuple[domain.RecipeBenchContentWeight, ...],
) -> str:
    if not weights:
        return "<p class=\"empty\">No content outliers.</p>"
    return "<ul class=\"tree\">" + "".join(
        "<li>"
        f"<code>{_escape(weight.path)}</code> "
        f"{weight.line_count} lines, {weight.symbol_count} symbols"
        f" - {_escape(weight.reason)}"
        "</li>"
        for weight in weights
    ) + "</ul>"


def _matrix_section(
    report: domain.RecipeBenchReport,
    residue_paths: tuple[str, ...],
) -> str:
    if not report.same_role_modules:
        return "<section><h2>Same-Role Matrix</h2><p>No modules to compare.</p></section>"
    if not residue_paths:
        return (
            "<section><h2>Same-Role Matrix</h2>"
            "<p>No residue paths were found across the same-role modules.</p></section>"
        )

    header_cells = "".join(
        f"<th><code>{_escape(path)}</code></th>"
        for path in residue_paths
    )
    rows = "".join(
        _matrix_row(report, bench_module, residue_paths)
        for bench_module in report.same_role_modules
    )
    return (
        "<section><h2>Same-Role Matrix</h2>"
        "<div class=\"table-wrap\"><table>"
        f"<thead><tr><th>Module</th>{header_cells}</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
        "</section>"
    )


def _matrix_row(
    report: domain.RecipeBenchReport,
    bench_module: domain.RecipeBenchModule,
    residue_paths: tuple[str, ...],
) -> str:
    residue_set = set(bench_module.residue_files)
    selected_class = (
        " class=\"selected\""
        if bench_module.module_name == report.selected_module
        else ""
    )
    cells = "".join(
        "<td class=\"hit\">yes</td>" if path in residue_set else "<td></td>"
        for path in residue_paths
    )
    return (
        f"<tr{selected_class}>"
        f"<th><code>{_escape(bench_module.module_name)}</code></th>"
        f"{cells}</tr>"
    )


def _recurrence_section(report: domain.RecipeBenchReport) -> str:
    return (
        "<section><h2>Recurrence</h2>"
        f"{_role_recurrence_bars('Forbidden residue', report.recurrence, report.same_role_module_count)}"
        f"{_role_recurrence_bars('Slot growth', report.slot_growth_recurrence, report.same_role_module_count)}"
        f"{_role_recurrence_bars('Content weight', report.content_weight_recurrence, report.same_role_module_count)}"
        "</section>"
    )


def _interpretation_section() -> str:
    return (
        "<section><h2>Interpretation</h2>"
        "<ul>"
        "<li>Unique residue is local warp stink.</li>"
        "<li>Allowed package internals still count as slot-growth pressure.</li>"
        "<li>Large or symbol-heavy files count as content-weight pressure.</li>"
        "<li>Repeated residue is undeclared pattern pressure.</li>"
        "<li>Very common residue suggests the recipe may be stale.</li>"
        "<li>Many unrelated residues suggest the role may be too broad.</li>"
        "</ul>"
        "</section>"
    )


def _classification_severity(classification: str) -> str:
    return {
        "clean": "clean",
        "local": "low",
        "emerging": "medium",
        "established": "high",
        "unstable": "critical",
    }.get(classification, "")


def _count_severity(count: int) -> str:
    return "high" if count else "clean"


def _summary_class(severity: str) -> str:
    return f"severity-card severity-{severity}" if severity else "severity-card"


def _row_class(severity: str) -> str:
    return f"severity-row severity-{severity}" if severity else "severity-row"


def _bar_class(severity: str) -> str:
    return f"severity-bar severity-{severity}" if severity else "severity-bar"


def _badge(value: str, severity: str) -> str:
    return (
        f"<span class=\"badge severity-{_escape(severity)}\">"
        f"{_escape(value)}</span>"
    )


def _count_cell(count: int) -> str:
    return (
        f"<td class=\"count severity-{_escape(_count_severity(count))}\">"
        f"{count}</td>"
    )


def _bench_css() -> str:
    return """
body {
  margin: 0;
  color: #1f2933;
  background: #f6f8fa;
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
main { max-width: 1180px; margin: 0 auto; padding: 32px; }
header, section {
  background: #ffffff;
  border: 1px solid #d8dee4;
  border-radius: 8px;
  margin-bottom: 18px;
  padding: 20px;
}
.eyebrow { color: #57606a; font-size: 12px; margin: 0 0 4px; text-transform: uppercase; }
h1, h2, h3 { margin: 0 0 14px; line-height: 1.2; }
h1 { font-size: 28px; }
h2 { font-size: 18px; }
h3 { font-size: 15px; }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; padding: 0; border: 0; margin: 16px 0 0; }
.summary div { background: #f6f8fa; border: 1px solid #d8dee4; border-radius: 6px; padding: 12px; }
.summary span { display: block; color: #57606a; font-size: 12px; }
.summary strong { display: block; font-size: 18px; margin-top: 4px; }
.severity-card.severity-clean { background: #eefaf0; border-color: #9be9a8; }
.severity-card.severity-low { background: #fff8c5; border-color: #eac54f; }
.severity-card.severity-medium { background: #fff1e5; border-color: #f69d50; }
.severity-card.severity-high { background: #ffebe9; border-color: #ff8182; }
.severity-card.severity-critical { background: #fbefff; border-color: #bf87ff; }
.columns { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
article { border: 1px solid #d8dee4; border-radius: 6px; padding: 14px; min-width: 0; }
.role-block { margin-top: 14px; }
.tree { list-style: none; margin: 0; padding: 0; }
.tree li { border-bottom: 1px solid #eef1f4; padding: 5px 0; overflow-wrap: anywhere; }
.empty { color: #57606a; }
.contents { margin-top: 16px; }
details { border-top: 1px solid #d8dee4; padding: 8px 0; }
summary { cursor: pointer; font-weight: 600; overflow-wrap: anywhere; }
pre { background: #0f1720; border-radius: 6px; color: #e6edf3; overflow: auto; padding: 12px; white-space: pre-wrap; }
code { font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; min-width: 100%; }
th, td { border: 1px solid #d8dee4; padding: 8px; text-align: left; vertical-align: top; }
thead th { background: #f6f8fa; }
tr.selected th, tr.selected td { background: #fff8c5; }
tr.severity-clean th, tr.severity-clean td { background: #fbfffc; }
tr.severity-low th, tr.severity-low td { background: #fffdf0; }
tr.severity-medium th, tr.severity-medium td { background: #fff8f2; }
tr.severity-high th, tr.severity-high td { background: #fff5f4; }
tr.severity-critical th, tr.severity-critical td { background: #fcf5ff; }
td.count { font-weight: 700; text-align: right; }
td.count.severity-clean { color: #1a7f37; }
td.count.severity-high { color: #cf222e; }
td.hit { background: #dafbe1; color: #116329; font-weight: 700; text-align: center; }
.badge { border-radius: 999px; display: inline-block; font-size: 12px; font-weight: 700; padding: 2px 8px; }
.badge.severity-clean { background: #dafbe1; color: #116329; }
.badge.severity-low { background: #fff8c5; color: #7d4e00; }
.badge.severity-medium { background: #ffdfb6; color: #953800; }
.badge.severity-high { background: #ffebe9; color: #cf222e; }
.badge.severity-critical { background: #fbefff; color: #8250df; }
.bar-row { display: grid; grid-template-columns: minmax(180px, 1fr) minmax(140px, 3fr) 130px; gap: 12px; align-items: center; margin: 10px 0; }
.bar-track { background: #eef1f4; border-radius: 999px; height: 12px; overflow: hidden; }
.bar-track span { display: block; height: 100%; }
.severity-bar.severity-clean { background: #2da44e; }
.severity-bar.severity-low { background: #d4a72c; }
.severity-bar.severity-medium { background: #fb8f44; }
.severity-bar.severity-high { background: #cf222e; }
.severity-bar.severity-critical { background: #8250df; }
@media (max-width: 820px) {
  main { padding: 16px; }
  .columns { grid-template-columns: 1fr; }
  .bar-row { grid-template-columns: 1fr; }
}
""".strip()


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


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
