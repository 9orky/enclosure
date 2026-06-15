from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from enclosure.shared import layout

from . import domain, infrastructure


class _RecipeGenerationService:
    def __init__(
        self,
        *,
        recipe_root: Path,
        config: domain.RecipeGenerationConfig,
    ) -> None:
        self._repository = infrastructure.FileRecipeRepository(recipe_root)
        self._config = config
        self._renderer = infrastructure.FileRecipeRenderer()
        self._materializer = infrastructure.FileRecipeMaterializer()

    def list_recipes(self) -> tuple[domain.RecipeSummary, ...]:
        return tuple(self._summarize_recipe(recipe) for recipe in self._repository.find_all())

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
            recipes = self._repository.find_all()
        except ValueError as exc:
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._repository.root_path,
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
                recipe_root=self._repository.root_path,
                recipes_discovered=len(recipes),
                recipes_checked=len(recipes),
                rendered_paths_checked=rendered_paths_checked,
                violations=tuple(violations),
            )

        recipe = self._load_recipe(recipe_name)
        if recipe is None:
            return domain.RecipeCheckReport(
                project_root=project_root,
                recipe_root=self._repository.root_path,
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

        rendered_paths_checked = self._check_recipe(
            violations,
            recipe,
            recipes_by_name=_recipes_by_name(recipes),
            project_root=project_root,
            target_path=target_path or Path("_enclosure_recipe_check") / recipe.name,
            variables=_check_variables_for(recipe, variables),
        )

        return domain.RecipeCheckReport(
            project_root=project_root,
            recipe_root=self._repository.root_path,
            recipes_discovered=len(recipes),
            recipes_checked=1,
            rendered_paths_checked=rendered_paths_checked,
            violations=tuple(violations),
        )

    def _check_recipe(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipe: domain.Recipe,
        *,
        recipes_by_name: Mapping[str, domain.Recipe],
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> int:
        self._validate_recipe_contract(violations, recipe, recipes_by_name)
        try:
            rendered_files = self._render_files(
                recipe,
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
        if recipe.role is domain.RecipeRole.CONTAINER:
            self._validate_container_composition(
                violations,
                recipe,
                recipes_by_name,
                project_root=project_root,
                target_path=target_path,
                variables=variables,
                container_files=rendered_files,
            )
        return len(create_paths) + len(skipped_paths)

    def _validate_recipe_contract(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipe: domain.Recipe,
        recipes_by_name: Mapping[str, domain.Recipe],
    ) -> None:
        if recipe.role is domain.RecipeRole.ARCHETYPE and recipe.archetypes:
            violations.append(
                domain.RecipeCheckViolation(
                    code="unexpected_archetypes",
                    message="Only container recipes may declare archetypes",
                    recipe_name=recipe.name,
                )
            )
            return
        if recipe.role is domain.RecipeRole.CONTAINER and not recipe.archetypes:
            violations.append(
                domain.RecipeCheckViolation(
                    code="missing_archetypes",
                    message="Container recipes must declare archetypes",
                    recipe_name=recipe.name,
                )
            )
            return
        if recipe.role is domain.RecipeRole.CONTAINER:
            for archetype_name in recipe.archetypes:
                archetype = recipes_by_name.get(archetype_name)
                if archetype is None:
                    violations.append(
                        domain.RecipeCheckViolation(
                            code="missing_archetype",
                            message=f"Container references missing archetype: {archetype_name}",
                            recipe_name=recipe.name,
                        )
                    )
                    continue
                if archetype.role is not domain.RecipeRole.ARCHETYPE:
                    violations.append(
                        domain.RecipeCheckViolation(
                            code="non_archetype_reference",
                            message=(
                                "Container archetypes must reference role: archetype "
                                f"recipes: {archetype_name}"
                            ),
                            recipe_name=recipe.name,
                        )
                    )

    def _validate_container_composition(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipe: domain.Recipe,
        recipes_by_name: Mapping[str, domain.Recipe],
        *,
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
        container_files: tuple[domain.RenderedFile, ...],
    ) -> None:
        if _has_contract_violations(violations, recipe.name):
            return

        archetype_files: list[domain.RenderedFile] = []
        for archetype_name in recipe.archetypes:
            archetype = recipes_by_name[archetype_name]
            try:
                archetype_files.extend(
                    self._render_files(
                        archetype,
                        project_root=project_root,
                        target_path=target_path,
                        variables=variables,
                    )
                )
            except ValueError as exc:
                violations.append(
                    domain.RecipeCheckViolation(
                        code="archetype_render_failed",
                        message=f"{archetype_name}: {exc}",
                        recipe_name=recipe.name,
                    )
                )
                return

        container_map = _rendered_file_map(container_files)
        archetype_map: dict[str, str] = {}
        for rendered_file in archetype_files:
            key = rendered_file["relative_path"].as_posix()
            existing_content = archetype_map.get(key)
            if existing_content is not None and existing_content != rendered_file["content"]:
                violations.append(
                    domain.RecipeCheckViolation(
                        code="duplicate_archetype_target",
                        message=f"Archetypes render conflicting content for {key}",
                        recipe_name=recipe.name,
                    )
                )
                return
            archetype_map[key] = rendered_file["content"]

        missing_paths = tuple(sorted(set(container_map) - set(archetype_map)))
        extra_paths = tuple(sorted(set(archetype_map) - set(container_map)))
        mismatched_paths = tuple(
            sorted(
                path
                for path in set(container_map) & set(archetype_map)
                if container_map[path] != archetype_map[path]
            )
        )
        if missing_paths or extra_paths or mismatched_paths:
            details = []
            if missing_paths:
                details.append("missing: " + ", ".join(missing_paths))
            if extra_paths:
                details.append("extra: " + ", ".join(extra_paths))
            if mismatched_paths:
                details.append("mismatch: " + ", ".join(mismatched_paths))
            violations.append(
                domain.RecipeCheckViolation(
                    code="composition_mismatch",
                    message="Container does not match archetype union; " + "; ".join(details),
                    recipe_name=recipe.name,
                )
            )

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
            }

        rendered_files = self._render_files(
            recipe,
            project_root=project_root,
            target_path=target_path,
            variables=variables,
        )
        create_paths, skipped_paths = self._plan_paths(rendered_files)
        return {
            "recipe_name": recipe.name,
            "project_root": project_root,
            "recipe_found": True,
            "recipe_empty": recipe.is_empty(),
            "create_paths": create_paths,
            "skipped_paths": skipped_paths,
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

        rendered_files = self._render_files(
            recipe,
            project_root=project_root,
            target_path=target_path,
            variables=variables,
        )
        create_paths, skipped_paths = self._plan_paths(rendered_files)
        self._materializer.write_files(rendered_files, create_paths=create_paths)

        return {
            "recipe_name": recipe.name,
            "project_root": project_root,
            "recipe_found": True,
            "recipe_empty": recipe.is_empty(),
            "created_paths": create_paths,
            "skipped_paths": skipped_paths,
        }

    def _load_recipe(self, recipe_name: str) -> domain.Recipe | None:
        try:
            return self._repository.get_by_name(recipe_name)
        except LookupError:
            return None

    def _render_files(
        self,
        recipe: domain.Recipe,
        *,
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> tuple[domain.RenderedFile, ...]:
        target_relative_path = domain.normalize_target_path(project_root, target_path)
        context = self._render_context(
            recipe,
            target_relative_path=target_relative_path,
            variables=variables,
        )

        return self._renderer.render_files(
            recipe,
            project_root=project_root,
            context=context,
        )

    def _render_context(
        self,
        recipe: domain.Recipe,
        *,
        target_relative_path: domain.RelativePath,
        variables: Mapping[str, str],
    ) -> dict[str, Any]:
        raw_variables = dict(variables)
        defaults = domain.defaults_for(target_relative_path)
        context: dict[str, Any] = {
            "target": domain.target_context_for(target_relative_path),
        }

        for input_spec in recipe.inputs:
            value = input_spec.resolve(raw_variables, defaults)
            context[input_spec.name] = domain.variable_context_for(input_spec.name, value)

        for name, value in raw_variables.items():
            if name not in context:
                context[name] = domain.variable_context_for(name, value)

        return context

    def _plan_paths(
        self,
        rendered_files: tuple[domain.RenderedFile, ...],
    ) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
        create_paths: list[Path] = []
        skipped_paths: list[Path] = []

        for rendered_file in rendered_files:
            target_path = rendered_file["target_path"]
            relative_path = rendered_file["relative_path"]
            if self._config.should_skip(relative_path):
                skipped_paths.append(target_path)
                continue
            if target_path.exists():
                skipped_paths.append(target_path)
                continue

            create_paths.append(target_path)

        return tuple(create_paths), tuple(skipped_paths)

    def _summarize_recipe(self, recipe: domain.Recipe) -> domain.RecipeSummary:
        return {
            "name": recipe.name,
            "description": recipe.description,
            "role": recipe.role.value,
            "archetypes": recipe.archetypes,
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
    project_root = layout.current_project_root()
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).generate(recipe_name, project_root, target_path, variables=variables)


def describe_recipe_generation(
    recipe_name: str,
    target_path: Path | str,
    *,
    recipe_root: Path,
    variables: Mapping[str, str],
) -> domain.RecipeGenerationReport:
    project_root = layout.current_project_root()
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
    project_root = layout.current_project_root()
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=domain.RecipeGenerationConfig(skip=()),
    ).check(
        project_root,
        recipe_name,
        target_path,
        variables=variables,
    )


def _load_recipe_generation_settings() -> domain.RecipeGenerationConfig:
    return infrastructure.load_recipe_generation_config()


def _check_variables_for(
    recipe: domain.Recipe,
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


def _sample_value_for(input_spec: domain.RecipeInputSpec) -> str:
    if input_spec.choices:
        return input_spec.choices[0]
    if input_spec.value_type == "list":
        return "sample"
    if input_spec.value_type == "path":
        return "sample"
    if input_spec.value_type == "dotted_name":
        return "sample"
    return "sample"


def _recipes_by_name(recipes: tuple[domain.Recipe, ...]) -> dict[str, domain.Recipe]:
    return {recipe.name: recipe for recipe in recipes}


def _rendered_file_map(
    rendered_files: tuple[domain.RenderedFile, ...],
) -> dict[str, str]:
    return {
        rendered_file["relative_path"].as_posix(): rendered_file["content"]
        for rendered_file in rendered_files
    }


def _has_contract_violations(
    violations: list[domain.RecipeCheckViolation],
    recipe_name: str,
) -> bool:
    contract_codes = {
        "unexpected_archetypes",
        "missing_archetypes",
        "missing_archetype",
        "non_archetype_reference",
    }
    return any(
        violation.recipe_name == recipe_name and violation.code in contract_codes
        for violation in violations
    )


RecipeGenerationConfig = domain.RecipeGenerationConfig
GenerateRecipeResult = domain.GenerateRecipeResult
RecipeCheckReport = domain.RecipeCheckReport
RecipeCheckViolation = domain.RecipeCheckViolation
RecipeGenerationReport = domain.RecipeGenerationReport
RecipeSummary = domain.RecipeSummary
parse_variables = domain.parse_variables
