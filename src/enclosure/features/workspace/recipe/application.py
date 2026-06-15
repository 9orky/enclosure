from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from enclosure.shared import config
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
        recipe: domain.Recipe,
        recipes_by_name: Mapping[str, domain.Recipe],
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
            recipe.role in {domain.RecipeRole.ARCHETYPE, domain.RecipeRole.FRAGMENT}
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
        if recipe.role is domain.RecipeRole.ARCHETYPE and recipe.archetypes:
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
            }
        recipes_by_name = _recipes_by_name(self._repository.find_all())

        rendered_files = self._render_files(
            recipe,
            recipes_by_name=recipes_by_name,
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
        recipes_by_name = _recipes_by_name(self._repository.find_all())

        rendered_files = self._render_files(
            recipe,
            recipes_by_name=recipes_by_name,
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
        recipes_by_name: Mapping[str, domain.Recipe],
        project_root: Path,
        target_path: Path | str,
        variables: Mapping[str, str],
    ) -> tuple[domain.RenderedFile, ...]:
        target_relative_path = domain.normalize_target_path(project_root, target_path)
        context = self._render_context(
            recipe,
            recipes_by_name=recipes_by_name,
            target_relative_path=target_relative_path,
            variables=variables,
        )

        rendered_files: list[domain.RenderedFile] = []
        for included_recipe in _recipes_for_rendering(recipe, recipes_by_name):
            rendered_files.extend(
                self._renderer.render_files(
                    included_recipe,
                    project_root=project_root,
                    context=context,
                )
            )
        return tuple(rendered_files)

    def _render_context(
        self,
        recipe: domain.Recipe,
        *,
        recipes_by_name: Mapping[str, domain.Recipe],
        target_relative_path: domain.RelativePath,
        variables: Mapping[str, str],
    ) -> dict[str, Any]:
        raw_variables = dict(variables)
        defaults = domain.defaults_for(target_relative_path)
        context: dict[str, Any] = {
            "target": domain.target_context_for(target_relative_path),
        }

        for input_spec in _input_specs_for(recipe, recipes_by_name):
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

    def drifts(self, project_root: Path) -> domain.RecipeDriftReport:
        project_root = Path(project_root).resolve()
        violations: list[domain.RecipeCheckViolation] = []
        try:
            recipes = self._repository.find_all()
        except ValueError as exc:
            return domain.RecipeDriftReport(
                project_root=project_root,
                recipe_root=self._repository.root_path,
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

            actual_files = _actual_files_for(module_path)
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
                    missing_files=missing_files,
                    extra_files=extra_files,
                )
            )

        for module_name in _actual_module_names(architecture_root):
            if module_name not in roles_map:
                drifts.append(
                    domain.RecipeDrift(
                        module_name=module_name,
                        role_name="",
                        extra_files=_actual_files_for(architecture_root / module_name),
                    )
                )

        return domain.RecipeDriftReport(
            project_root=project_root,
            recipe_root=self._repository.root_path,
            architecture_root=architecture_root,
            modules_checked=len(drifts),
            drifts=tuple(drifts),
            violations=tuple(violations),
        )

    def _summarize_recipe(self, recipe: domain.Recipe) -> domain.RecipeSummary:
        return {
            "name": recipe.name,
            "description": recipe.description,
            "role": recipe.role.value,
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
    project_root = layout.current_project_root()
    return _RecipeGenerationService(
        recipe_root=recipe_root,
        config=_load_recipe_generation_settings(),
    ).drifts(project_root)


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


def _recipe_for_role(
    role_name: str,
    recipes_by_name: Mapping[str, domain.Recipe],
) -> domain.Recipe | None:
    if "+" not in role_name:
        return recipes_by_name.get(role_name)

    include_names = tuple(part.strip() for part in role_name.split("+") if part.strip())
    if not include_names:
        return None
    if any(include_name not in recipes_by_name for include_name in include_names):
        return None
    if any(
        recipes_by_name[include_name].role is domain.RecipeRole.CONTAINER
        for include_name in include_names
    ):
        return None
    return domain.Recipe(
        name="composed-role",
        root_path=Path("."),
        role=domain.RecipeRole.ARCHETYPE,
        description="Composed recipe role",
        ladder=domain.RecipeLadder(
            family="composed",
            rung=role_name,
            declared=True,
        ),
        includes=include_names,
    )


def _recipes_for_rendering(
    recipe: domain.Recipe,
    recipes_by_name: Mapping[str, domain.Recipe],
) -> tuple[domain.Recipe, ...]:
    return _included_recipes_for(recipe, recipes_by_name, trail=()) + (recipe,)


def _included_recipes_for(
    recipe: domain.Recipe,
    recipes_by_name: Mapping[str, domain.Recipe],
    *,
    trail: tuple[str, ...],
) -> tuple[domain.Recipe, ...]:
    recipes: list[domain.Recipe] = []
    for include_name in recipe.includes:
        if include_name in trail:
            cycle = " -> ".join(trail + (include_name,))
            raise ValueError(f"Recipe include cycle: {cycle}")
        included_recipe = recipes_by_name.get(include_name)
        if included_recipe is None:
            raise ValueError(f"Recipe include not found: {include_name}")
        recipes.extend(
            _included_recipes_for(
                included_recipe,
                recipes_by_name,
                trail=trail + (recipe.name,),
            )
        )
        recipes.append(included_recipe)
    return tuple(recipes)


def _input_specs_for(
    recipe: domain.Recipe,
    recipes_by_name: Mapping[str, domain.Recipe],
) -> tuple[domain.RecipeInputSpec, ...]:
    input_specs: list[domain.RecipeInputSpec] = []
    for included_recipe in _included_recipes_for(recipe, recipes_by_name, trail=()):
        input_specs.extend(included_recipe.inputs)
    input_specs.extend(recipe.inputs)
    return tuple(input_specs)


def _composed_ladder_for(
    recipe: domain.Recipe,
    recipes_by_name: Mapping[str, domain.Recipe],
) -> domain.RecipeLadder:
    slots_by_name: dict[str, domain.RecipeSlot] = {}
    for included_recipe in _included_recipes_for(recipe, recipes_by_name, trail=()):
        for slot in included_recipe.ladder.slots:
            slots_by_name[slot.name.value] = slot
    for slot in recipe.ladder.slots:
        slots_by_name[slot.name.value] = slot

    return domain.RecipeLadder(
        family=recipe.ladder.family,
        rung=recipe.ladder.rung,
        slots=tuple(slots_by_name.values()),
        declared=recipe.ladder.is_declared(),
    )


def _validate_recipe_catalog(
    violations: list[domain.RecipeCheckViolation],
    recipes: tuple[domain.Recipe, ...],
    recipes_by_name: Mapping[str, domain.Recipe],
) -> None:
    containers = tuple(
        recipe for recipe in recipes if recipe.role is domain.RecipeRole.CONTAINER
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
        recipe.name for recipe in recipes if recipe.role is domain.RecipeRole.ARCHETYPE
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
    recipes_by_name: Mapping[str, domain.Recipe],
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
    recipes: tuple[domain.Recipe, ...],
    recipes_by_name: Mapping[str, domain.Recipe],
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
            if included_recipe.role is domain.RecipeRole.CONTAINER:
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
    recipes_by_name: Mapping[str, domain.Recipe],
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
        if archetype.role is not domain.RecipeRole.ARCHETYPE:
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
    recipes_by_name: Mapping[str, domain.Recipe],
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
        if "+" not in role_name and role_recipe.role is not domain.RecipeRole.ARCHETYPE:
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
    config_path = project_root / ".enclosure" / "enclosure.yaml"
    raw_data = config.load_yaml_mapping(
        config_path,
        label="Config file",
        error_type=RuntimeError,
    )
    architecture = raw_data.get("architecture")
    if not isinstance(architecture, dict):
        raise RuntimeError(f"Missing architecture config section in {config_path}")
    root = architecture.get("root")
    if not isinstance(root, str) or not root.strip():
        raise RuntimeError(f"Missing architecture.root in {config_path}")
    return project_root / root


def _expected_files_for(
    service: _RecipeGenerationService,
    recipe: domain.Recipe,
    *,
    recipes_by_name: Mapping[str, domain.Recipe],
    project_root: Path,
    target_path: Path,
) -> set[str]:
    target_relative_path = domain.normalize_target_path(project_root, target_path)
    rendered_files = service._render_files(
        recipe,
        recipes_by_name=recipes_by_name,
        project_root=project_root,
        target_path=target_relative_path.value,
        variables={},
    )
    prefix = target_relative_path.as_posix() + "/"
    return {
        rendered_file["relative_path"].as_posix().removeprefix(prefix)
        for rendered_file in rendered_files
    }


def _drift_files_for(
    recipe: domain.Recipe,
    *,
    recipes_by_name: Mapping[str, domain.Recipe],
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
    forbidden_files: set[str] = set()
    forbidden_prefixes: set[str] = set()

    for slot in ladder.slots:
        slot_path = slot.name.value
        if slot.state is domain.RecipeSlotState.ABSENT:
            forbidden_files.add(f"{slot_path}.py")
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot.state is domain.RecipeSlotState.FILE:
            required_files.add(f"{slot_path}.py")
            allowed_files.add(f"{slot_path}.py")
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot.state is domain.RecipeSlotState.PACKAGE:
            required_files.add(f"{slot_path}/__init__.py")
            allowed_files.add(f"{slot_path}/__init__.py")
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_files.add(f"{slot_path}.py")
            continue

        if slot.state is domain.RecipeSlotState.SPLIT_FILES:
            required_files.add(f"{slot_path}/__init__.py")
            allowed_files.add(f"{slot_path}/__init__.py")
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_files.add(f"{slot_path}.py")
            for slot_file in slot.files:
                slot_file_path = f"{slot_path}/{slot_file}"
                required_files.add(slot_file_path)
                allowed_files.add(slot_file_path)
                if Path(slot_file).suffix:
                    forbidden_prefixes.add(
                        f"{slot_path}/{Path(slot_file).with_suffix('').as_posix()}/"
                    )
            continue

        if slot.state is domain.RecipeSlotState.SPLIT_PACKAGES:
            required_files.add(f"{slot_path}/__init__.py")
            allowed_files.add(f"{slot_path}/__init__.py")
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_files.add(f"{slot_path}.py")
            for slot_package in slot.packages:
                slot_package_path = f"{slot_path}/{slot_package}"
                required_files.add(f"{slot_package_path}/__init__.py")
                allowed_files.add(f"{slot_package_path}/__init__.py")
                allowed_prefixes.add(f"{slot_package_path}/")
                forbidden_files.add(f"{slot_package_path}.py")

    missing_files = tuple(sorted(required_files - actual_files))
    extra_files = tuple(
        sorted(
            actual_file
            for actual_file in actual_files
            if _is_extra_ladder_file(
                actual_file,
                allowed_files=allowed_files,
                allowed_prefixes=allowed_prefixes,
                forbidden_files=forbidden_files,
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
    forbidden_files: set[str],
    forbidden_prefixes: set[str],
) -> bool:
    if actual_file in forbidden_files:
        return True
    if any(actual_file.startswith(prefix) for prefix in forbidden_prefixes):
        return True
    if actual_file in allowed_files:
        return False
    return not any(actual_file.startswith(prefix) for prefix in allowed_prefixes)


def _actual_files_for(module_path: Path) -> set[str]:
    return {
        path.relative_to(module_path).as_posix()
        for path in module_path.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def _actual_module_names(architecture_root: Path) -> tuple[str, ...]:
    return tuple(
        module_path.relative_to(architecture_root).as_posix()
        for module_path in sorted(architecture_root.glob("*/*"))
        if module_path.is_dir() and (module_path / "__init__.py").is_file()
    )


RecipeGenerationConfig = domain.RecipeGenerationConfig
GenerateRecipeResult = domain.GenerateRecipeResult
RecipeCheckReport = domain.RecipeCheckReport
RecipeCheckViolation = domain.RecipeCheckViolation
RecipeDrift = domain.RecipeDrift
RecipeDriftReport = domain.RecipeDriftReport
RecipeGenerationReport = domain.RecipeGenerationReport
RecipeSummary = domain.RecipeSummary
parse_variables = domain.parse_variables
