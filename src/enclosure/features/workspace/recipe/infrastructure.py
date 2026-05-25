from __future__ import annotations

from pathlib import Path
from typing import Any

from enclosure.shared import config, templates

from . import domain


def load_recipe_generation_config() -> domain.RecipeGenerationConfig:
    _project_root, config_path, raw_data = config.load_project_mapping()
    return config.section(
        raw_data,
        "workspace.recipe",
        domain.RecipeConfig,
        config_path,
    )


class FileRecipeRepository:
    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def find_all(self) -> tuple[domain.Recipe, ...]:
        if not self.root_path.is_dir():
            return ()

        return tuple(
            self._load_recipe(recipe_root)
            for recipe_root in sorted(
                self._iter_recipe_roots(),
                key=lambda path: path.name,
            )
        )

    def get_by_name(self, name: str) -> domain.Recipe:
        recipe_root = self.root_path / name
        if not (recipe_root / "recipe.yaml").is_file():
            raise LookupError(name)

        return self._load_recipe(recipe_root)

    def _iter_recipe_roots(self):
        for child in self.root_path.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir() and (child / "recipe.yaml").is_file():
                yield child

    def _load_recipe(self, recipe_root: Path) -> domain.Recipe:
        manifest_path = recipe_root / "recipe.yaml"
        raw_data = config.load_yaml_mapping(
            manifest_path,
            label="Recipe manifest",
            error_type=ValueError,
        )
        return _recipe_from_manifest(recipe_root, raw_data)


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


def _recipe_from_manifest(recipe_root: Path, raw_data: dict[str, Any]) -> domain.Recipe:
    schema_version = raw_data.get("schema_version")
    if schema_version != 1:
        raise ValueError(
            f"Unsupported recipe schema_version in {recipe_root / 'recipe.yaml'}"
        )

    inputs = tuple(_input_specs_from(raw_data.get("inputs", {})))
    files = tuple(_recipe_files_from(raw_data.get("files", ())))

    return domain.Recipe(
        name=recipe_root.name,
        root_path=recipe_root,
        description=str(raw_data.get("description", "") or ""),
        inputs=inputs,
        files=files,
    )


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
