from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from enclosure.shared import templates

from . import domain


class _RecipeManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    role: domain.RecipeRole
    description: str = ""
    ladder: dict[str, Any] = Field(default_factory=dict)
    includes: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    roles_map: dict[str, str] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    files: list[dict[str, Any]] = Field(default_factory=list)


class FileRecipeRepository:
    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def find_all(self) -> tuple[domain.Recipe, ...]:
        if not self.root_path.is_dir():
            return ()

        return tuple(
            self._load_recipe(recipe_root, _recipe_manifest_path(recipe_root))
            for recipe_root in sorted(
                self._iter_recipe_roots(),
                key=lambda path: path.name,
            )
        )

    def get_by_name(self, name: str) -> domain.Recipe:
        recipe_root = self.root_path / name
        manifest_path = _recipe_manifest_path(recipe_root)
        if not manifest_path.is_file():
            raise LookupError(name)

        return self._load_recipe(recipe_root, manifest_path)

    def _iter_recipe_roots(self):
        for child in self.root_path.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir() and _recipe_manifest_path(child).is_file():
                yield child

    def _load_recipe(self, recipe_root: Path, manifest_path: Path) -> domain.Recipe:
        raw_data = _load_yaml_mapping(manifest_path)
        return _recipe_from_manifest(recipe_root, manifest_path, raw_data)


class FileRecipeRenderer:
    def render_files(
        self,
        recipe: domain.Recipe,
        *,
        project_root: Path,
        context: dict[str, Any],
    ) -> tuple[domain.RenderedFile, ...]:
        rendered_files: list[domain.RenderedFile] = []
        for recipe_file in recipe.files:
            source_path = recipe_file.source.resolve_from(recipe.root_path)
            if not source_path.is_file():
                raise ValueError(f"Recipe template does not exist: {source_path}")

            rendered_target = templates.render_recipe_template(
                recipe_file.target,
                context,
            )
            relative_path = domain.normalize_rendered_target(rendered_target)
            content = templates.render_recipe_template(
                source_path.read_text(encoding="utf-8"),
                context,
            )
            rendered_files.append(
                {
                    "source_path": source_path,
                    "target_path": relative_path.resolve_from(project_root),
                    "relative_path": relative_path,
                    "content": content,
                }
            )

        return tuple(rendered_files)


class FileRecipeMaterializer:
    def write_files(
        self,
        rendered_files: tuple[domain.RenderedFile, ...],
        *,
        create_paths: tuple[Path, ...],
    ) -> None:
        create_path_set = set(create_paths)
        for rendered_file in rendered_files:
            if rendered_file["target_path"] not in create_path_set:
                continue
            rendered_file["target_path"].parent.mkdir(parents=True, exist_ok=True)
            rendered_file["target_path"].write_text(
                rendered_file["content"],
                encoding="utf-8",
            )


def _recipe_from_manifest(
    recipe_root: Path,
    manifest_path: Path,
    raw_data: dict[str, Any],
) -> domain.Recipe:
    try:
        manifest = _RecipeManifest.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid recipe manifest: {exc}") from exc

    if manifest.schema_version != 1:
        raise ValueError(f"Unsupported recipe schema_version in {manifest_path}")

    inputs = tuple(_input_specs_from(manifest.inputs))
    files = tuple(_recipe_files_from(manifest.files))

    return domain.Recipe(
        name=recipe_root.name,
        root_path=recipe_root,
        description=manifest.description,
        role=manifest.role,
        ladder=_recipe_ladder_from(manifest.ladder),
        includes=_recipe_includes_from(manifest.includes),
        archetypes=_recipe_archetypes_from(manifest.archetypes),
        roles_map=manifest.roles_map,
        inputs=inputs,
        files=files,
    )


def _recipe_manifest_path(recipe_root: Path) -> Path:
    return recipe_root / "recipe.yaml"


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ValueError(f"Could not read recipe manifest: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid recipe manifest syntax in {path}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError(f"Recipe manifest must contain a mapping at the top level: {path}")
    return raw_data


def _input_specs_from(raw_inputs: Any) -> tuple[domain.RecipeInputSpec, ...]:
    if raw_inputs is None:
        return ()
    if not isinstance(raw_inputs, dict):
        raise ValueError("Recipe inputs must be a mapping")

    specs: list[domain.RecipeInputSpec] = []
    for name, raw_spec in raw_inputs.items():
        if raw_spec is None:
            raw_spec = {}
        if not isinstance(name, str) or not isinstance(raw_spec, dict):
            raise ValueError("Recipe inputs must be named mappings")

        specs.append(
            domain.RecipeInputSpec(
                name=name,
                value_type=str(raw_spec.get("type", "string") or "string"),
                required=bool(raw_spec.get("required", False)),
                default=_optional_string(raw_spec.get("default")),
                default_from=_optional_string(raw_spec.get("default_from")),
                choices=_string_list(
                    raw_spec.get("choices", []),
                    f"Recipe input choices must be strings: {name}",
                ),
            )
        )
    return tuple(specs)


def _recipe_files_from(raw_files: Any) -> tuple[domain.RecipeFile, ...]:
    if raw_files is None:
        return ()
    if not isinstance(raw_files, list):
        raise ValueError("Recipe files must be a list")

    files: list[domain.RecipeFile] = []
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise ValueError("Recipe files must be mappings")
        source = raw_file.get("source")
        target = raw_file.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("Recipe files require source and target")
        files.append(domain.RecipeFile(domain.RelativePath(Path(source)), target))
    return tuple(files)


def _recipe_archetypes_from(raw_archetypes: Any) -> tuple[str, ...]:
    return _string_list(raw_archetypes, "Recipe archetypes must be strings")


def _recipe_includes_from(raw_includes: Any) -> tuple[str, ...]:
    return _string_list(raw_includes, "Recipe includes must be strings")


def _recipe_ladder_from(raw_ladder: Any) -> domain.RecipeLadder:
    if raw_ladder == {}:
        return domain.RecipeLadder()
    if not isinstance(raw_ladder, dict):
        raise ValueError("Recipe ladder must be a mapping")

    family = raw_ladder.get("family")
    rung = raw_ladder.get("rung")
    raw_slots = raw_ladder.get("slots", {})
    if not isinstance(family, str) or not isinstance(rung, str):
        raise ValueError("Recipe ladder requires family and rung")
    if not isinstance(raw_slots, dict):
        raise ValueError("Recipe ladder slots must be a mapping")

    slots = tuple(_recipe_slot_from(name, value) for name, value in raw_slots.items())
    return domain.RecipeLadder(
        family=family,
        rung=rung,
        slots=slots,
        declared=True,
    )


def _recipe_slot_from(raw_name: Any, raw_slot: Any) -> domain.RecipeSlot:
    if not isinstance(raw_name, str):
        raise ValueError("Recipe ladder slot names must be strings")

    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    if isinstance(raw_slot, str):
        raw_state = raw_slot
    elif isinstance(raw_slot, dict):
        raw_state = raw_slot.get("state")
        files = _string_list(
            raw_slot.get("files", []),
            f"Recipe ladder slot files must be strings: {raw_name}",
        )
        packages = _string_list(
            raw_slot.get("packages", []),
            f"Recipe ladder slot packages must be strings: {raw_name}",
        )
    else:
        raise ValueError("Recipe ladder slot values must be strings or mappings")

    if not isinstance(raw_state, str):
        raise ValueError(f"Recipe ladder slot requires state: {raw_name}")
    try:
        state = domain.RecipeSlotState(raw_state)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported recipe ladder state for {raw_name}: {raw_state}"
        ) from exc

    return domain.RecipeSlot(
        name=domain.RecipeSlotName(raw_name),
        state=state,
        files=files,
        packages=packages,
    )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_list(value: Any, message: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(message)
    return tuple(value)
