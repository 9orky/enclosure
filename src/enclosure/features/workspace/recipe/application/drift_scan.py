from __future__ import annotations

from pathlib import Path

from enclosure.features.architecture import flow
from .. import domain


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


def actual_module_names(
    architecture_root: Path,
    *,
    project_root: Path,
    config: domain.RecipeGenerationConfig,
    architecture_settings: object,
) -> tuple[str, ...]:
    return tuple(
        module_path.relative_to(architecture_root).as_posix()
        for module_path in _actual_module_paths(
            architecture_root,
            architecture_settings,
        )
        if module_path.is_dir()
        and actual_files_for(
            module_path,
            project_root=project_root,
            config=config,
        )
    )


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


def _actual_module_paths(
    architecture_root: Path,
    architecture_settings: object,
) -> tuple[Path, ...]:
    tag_rules = {
        getattr(rule, "name", ""): rule
        for rule in getattr(getattr(architecture_settings, "rules", object()), "tags", ())
    }
    paths: list[Path] = []
    for tag_name in _recipe_subject_tag_names(architecture_settings):
        tag_rule = tag_rules.get(tag_name)
        if tag_rule is None:
            continue
        paths.extend(architecture_root.glob(getattr(tag_rule, "match", "")))
    return tuple(dict.fromkeys(sorted(paths)))


def _recipe_subject_tag_names(architecture_settings: object) -> tuple[str, ...]:
    return tuple(
        realm.module_tag
        for realm in flow.configured_realms(architecture_settings)
        if realm.layers
    )


__all__ = [
    "actual_files_for",
    "actual_module_names",
]
