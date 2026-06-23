from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from enclosure.shared.scaffolding import Scaffold
from .. import domain, infrastructure


@dataclass(frozen=True)
class _ComposedLadder:
    family: str = ""
    rung: str = ""
    slots: tuple[Any, ...] = ()
    declared: bool = False

    def is_declared(self) -> bool:
        return self.declared



class RecipeCatalog:
    def __init__(self, workspace: infrastructure.RecipeWorkspace) -> None:
        self._workspace = workspace

    def list_recipes(self) -> tuple[domain.RecipeSummary, ...]:
        return tuple(summarize_recipe(recipe) for recipe in self._workspace.load_recipes())

    def show_recipe(self, recipe_name: str) -> domain.RecipeSummary | None:
        recipe = self._workspace.load_recipe(recipe_name)
        if recipe is None:
            return None
        return summarize_recipe(recipe)

    def validate_catalog(
        self,
        violations: list[domain.RecipeCheckViolation],
        recipes: tuple[Scaffold, ...],
        recipes_by_name: Mapping[str, Scaffold],
    ) -> None:
        validate_recipe_catalog(violations, recipes, recipes_by_name)

    def validate_roles_map(
        self,
        violations: list[domain.RecipeCheckViolation],
        *,
        roles_map: Mapping[str, str],
        recipes_by_name: Mapping[str, Scaffold],
    ) -> None:
        validate_config_roles_map(
            violations,
            roles_map=roles_map,
            recipes_by_name=recipes_by_name,
        )

    def recipe_for_role(
        self,
        role_name: str,
        recipes_by_name: Mapping[str, Scaffold],
    ) -> Scaffold | None:
        return recipe_for_role(role_name, recipes_by_name)

    def sample_variables(
        self,
        recipe: Scaffold,
        recipes_by_name: Mapping[str, Scaffold],
    ) -> dict[str, str]:
        return sample_variables_for_rendering(recipe, recipes_by_name)


def summarize_recipe(recipe: Scaffold) -> domain.RecipeSummary:
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


def check_variables_for(
    recipe: Scaffold,
    variables: Mapping[str, str],
) -> dict[str, str]:
    check_variables = dict(variables)
    for input_spec in recipe.inputs:
        if input_spec.name in check_variables:
            continue
        if not input_spec.required:
            continue
        check_variables[input_spec.name] = sample_value_for(input_spec)
    return check_variables


def sample_variables_for_rendering(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> dict[str, str]:
    variables: dict[str, str] = {}
    for input_spec in composed_recipe_inputs(recipe, recipes_by_name):
        if not input_spec.required or input_spec.name in variables:
            continue
        variables[input_spec.name] = sample_value_for(input_spec)
    return variables


def sample_value_for(input_spec: Any) -> str:
    if input_spec.choices:
        return input_spec.choices[0]
    if input_spec.value_type == "list":
        return "sample"
    if input_spec.value_type == "path":
        return "sample"
    if input_spec.value_type == "dotted_name":
        return "sample"
    return "sample"


def paths_from_preview_files(
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



def recipes_by_name(recipes: tuple[Scaffold, ...]) -> dict[str, Scaffold]:
    return {recipe.name: recipe for recipe in recipes}


def recipe_for_role(
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


def composed_recipe_inputs(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> tuple[Any, ...]:
    composed_recipes = infrastructure.compose_recipes(
        recipe,
        tuple(recipes_by_name.values()),
    )
    return tuple(input_spec for scaffold in composed_recipes for input_spec in scaffold.inputs)


def composed_ladder_for(
    recipe: Scaffold,
    recipes_by_name: Mapping[str, Scaffold],
) -> Any:
    slots_by_name: dict[str, Any] = {}
    for composed_recipe in infrastructure.compose_recipes(
        recipe,
        tuple(recipes_by_name.values()),
    ):
        for slot in composed_recipe.ladder.slots:
            slots_by_name[slot_name(slot)] = slot
    return _ComposedLadder(
        family=recipe.ladder.family,
        rung=recipe.ladder.rung,
        slots=tuple(slots_by_name.values()),
        declared=recipe.ladder.is_declared(),
    )


def slot_name(slot: Any) -> str:
    name = slot.name
    return name.value if hasattr(name, "value") else str(name)


def slot_state(slot: Any) -> str:
    state = slot.state
    return state.value if hasattr(state, "value") else str(state)


def relative_path_text(path: Path | str) -> str:
    return Path(path).as_posix().strip("/")


def validate_recipe_catalog(
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


def validate_config_roles_map(
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
        role_recipe = recipe_for_role(role_name, recipes_by_name)
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




__all__ = [
    "RecipeCatalog",
    "check_variables_for",
    "composed_ladder_for",
    "recipe_for_role",
    "recipes_by_name",
    "relative_path_text",
    "sample_variables_for_rendering",
    "slot_name",
    "slot_state",
    "validate_config_roles_map",
    "validate_recipe_catalog",
]
