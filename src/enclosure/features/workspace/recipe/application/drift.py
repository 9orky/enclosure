from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from enclosure.shared.scaffolding import RenderedScaffoldFile, Scaffold, ScaffoldError
from .. import domain, infrastructure
from . import catalog


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

        for module_name in actual_module_names(
            subject_root,
            project_root=project_root,
            config=self._workspace.config(),
        ):
            if module_name not in roles_map:
                drifts.append(
                    domain.RecipeDrift(
                        module_name=module_name,
                        role_name="",
                        extra_files=actual_files_for(
                            subject_root / module_name,
                            project_root=project_root,
                            config=self._workspace.config(),
                        ),
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




def drift_files_for(
    recipe: Scaffold,
    *,
    recipes_by_name: Mapping[str, Scaffold],
    expected_files: set[str],
    actual_files: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ladder = catalog.composed_ladder_for(recipe, recipes_by_name)
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
        slot_path = catalog.slot_name(slot)
        slot_state_value = catalog.slot_state(slot)
        if slot_state_value == "absent":
            forbidden_file_stems.add(slot_path)
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot_state_value == "file":
            forbidden_prefixes.add(f"{slot_path}/")
            continue

        if slot_state_value == "package":
            allowed_prefixes.add(f"{slot_path}/")
            forbidden_file_stems.add(slot_path)
            continue

        if slot_state_value == "split-files":
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

        if slot_state_value == "split-packages":
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


def actual_files_for(
    module_path: Path,
    *,
    project_root: Path,
    config: domain.RecipeGenerationConfig,
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
    project_root: Path,
    config: domain.RecipeGenerationConfig,
) -> bool:
    relative_candidates = [
        path.relative_to(module_path),
        path.relative_to(project_root),
    ]
    return any(
        config.should_skip(relative_path)
        for relative_path in relative_candidates
    )


def actual_module_names(
    architecture_root: Path,
    *,
    project_root: Path,
    config: domain.RecipeGenerationConfig,
) -> tuple[str, ...]:
    return tuple(
        module_path.relative_to(architecture_root).as_posix()
        for module_path in sorted(architecture_root.glob("*/*"))
        if module_path.is_dir()
        and actual_files_for(
            module_path,
            project_root=project_root,
            config=config,
        )
    )




__all__ = [
    "RecipeDriftService",
    "actual_files_for",
    "actual_module_names",
    "drift_files_for",
    "expected_files_for",
    "module_relative_rendered_paths",
]
