from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, TypedDict

from pydantic import field_validator

from enclosure.shared import config, naming

_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTTED_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RelativePath:
    value: Path

    def __post_init__(self) -> None:
        normalized_value = Path(str(self.value).replace("\\", "/"))
        if normalized_value.is_absolute():
            raise ValueError("Recipe paths must be relative")
        if not normalized_value.parts:
            raise ValueError("Recipe paths must not be empty")
        if any(part in {".", ".."} for part in normalized_value.parts):
            raise ValueError("Recipe paths must not traverse outside the target root")
        object.__setattr__(self, "value", normalized_value)

    def as_posix(self) -> str:
        return self.value.as_posix()

    def resolve_from(self, root_path: Path) -> Path:
        return root_path / self.value


class RecipeConfig(config.StrictConfigModel):
    skip: tuple[str, ...]

    @property
    def skip_globs(self) -> tuple[str, ...]:
        return self.skip

    @field_validator("skip")
    @classmethod
    def normalize_skip_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            value.strip().replace("\\", "/")
            for value in values
            if value.strip()
        )

    def should_skip(self, relative_path: RelativePath) -> bool:
        relative_path_text = relative_path.as_posix()
        return any(fnmatch(relative_path_text, pattern) for pattern in self.skip)


RecipeGenerationConfig = RecipeConfig


@dataclass(frozen=True)
class RecipeCheckViolation:
    code: str
    message: str
    recipe_name: str = ""


@dataclass(frozen=True)
class RecipeCheckReport:
    project_root: Path
    recipe_root: Path
    recipes_discovered: int
    recipes_checked: int
    rendered_paths_checked: int
    violations: tuple[RecipeCheckViolation, ...] = ()

    def passed(self) -> bool:
        return not self.violations


@dataclass(frozen=True)
class RecipeInputSpec:
    name: str
    value_type: str = "string"
    required: bool = False
    default: str = ""
    default_from: str = ""
    choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not _VARIABLE_NAME_PATTERN.match(normalized_name):
            raise ValueError(f"Invalid recipe input name: {self.name}")

        normalized_type = self.value_type.strip() or "string"
        supported_types = {
            "string",
            "identifier",
            "path",
            "dotted_name",
            "slug",
            "choice",
            "list",
        }
        if normalized_type not in supported_types:
            raise ValueError(f"Unsupported input type for {normalized_name}: {normalized_type}")

        if normalized_type == "choice" and not self.choices:
            raise ValueError(f"Choice input must declare choices: {normalized_name}")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "value_type", normalized_type)

    def resolve(self, raw_variables: dict[str, str], defaults: dict[str, str]) -> Any:
        if self.name in raw_variables:
            value = raw_variables[self.name]
        elif self.default_from and self.default_from in defaults:
            value = defaults[self.default_from]
        elif self.default:
            value = self.default
        elif self.required:
            raise ValueError(f"Missing required recipe variable: {self.name}")
        else:
            value = ""

        return self._validate(value)

    def _validate(self, value: str) -> Any:
        if self.value_type == "list":
            return tuple(item.strip() for item in value.split(",") if item.strip())

        normalized_value = value.strip()
        if self.value_type == "identifier" and not _IDENTIFIER_PATTERN.match(normalized_value):
            raise ValueError(f"Recipe variable {self.name} must be an identifier")
        if self.value_type == "dotted_name" and not _DOTTED_NAME_PATTERN.match(normalized_value):
            raise ValueError(f"Recipe variable {self.name} must be a dotted name")
        if self.value_type == "path":
            RelativePath(Path(normalized_value))
        if (
            self.value_type == "slug"
            and normalized_value != naming.kebab_case(normalized_value)
        ):
            raise ValueError(f"Recipe variable {self.name} must be a kebab-case slug")
        if self.value_type == "choice" and normalized_value not in self.choices:
            choices = ", ".join(self.choices)
            raise ValueError(f"Recipe variable {self.name} must be one of: {choices}")
        return normalized_value


@dataclass(frozen=True)
class RecipeFile:
    source: RelativePath
    target: str

    def __post_init__(self) -> None:
        normalized_target = self.target.strip()
        if not normalized_target:
            raise ValueError("Recipe files must declare a target")
        object.__setattr__(self, "target", normalized_target)


@dataclass(frozen=True)
class Recipe:
    name: str
    root_path: Path
    description: str = ""
    inputs: tuple[RecipeInputSpec, ...] = ()
    files: tuple[RecipeFile, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValueError("Recipe names must not be empty")

        name_path = Path(normalized_name)
        if len(name_path.parts) != 1 or name_path.parts[0] in {".", ".."}:
            raise ValueError("Recipe names must be a single folder name")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "root_path", Path(self.root_path))
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(self, "files", tuple(self.files))

    def is_empty(self) -> bool:
        return len(self.files) == 0


class RenderedFile(TypedDict):
    source_path: Path
    target_path: Path
    relative_path: RelativePath
    content: str


class RecipeGenerationReport(TypedDict):
    recipe_name: str
    project_root: Path
    recipe_found: bool
    recipe_empty: bool
    create_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]


class GenerateRecipeResult(TypedDict):
    recipe_name: str
    project_root: Path
    recipe_found: bool
    recipe_empty: bool
    created_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]


class RecipeSummary(TypedDict):
    name: str
    description: str
    inputs: tuple[str, ...]
    files: tuple[str, ...]


def variable_context_for(name: str, value: Any) -> Any:
    if isinstance(value, tuple):
        return value

    text = str(value)
    return {
        "value": text,
        "class": naming.pascal_case(text),
        "pascal": naming.pascal_case(text),
        "camel": naming.camel_case(text),
        "variable": naming.camel_case(text),
        "snake": naming.snake_case(text),
        "kebab": naming.kebab_case(text),
        "slug": naming.kebab_case(text),
        "upper": text.upper(),
        "lower": text.lower(),
        "name": text,
    }


def target_context_for(relative_path: RelativePath) -> dict[str, Any]:
    text = relative_path.as_posix()
    name = relative_path.value.name
    parts = relative_path.value.parts
    return {
        "path": text,
        "name": name,
        "class": naming.pascal_case(name),
        "pascal": naming.pascal_case(name),
        "camel": naming.camel_case(name),
        "variable": naming.camel_case(name),
        "snake": naming.snake_case(name),
        "kebab": naming.kebab_case(name),
        "slug": naming.kebab_case(name),
        "parts": parts,
        "parent": relative_path.value.parent.as_posix()
        if relative_path.value.parent != Path(".")
        else "",
    }


def normalize_target_path(project_root: Path, target_path: Path | str) -> RelativePath:
    project_root = Path(project_root).resolve()
    raw_path = Path(target_path)
    if not raw_path.is_absolute():
        return RelativePath(raw_path)

    try:
        return RelativePath(raw_path.resolve(strict=False).relative_to(project_root))
    except ValueError as exc:
        raise ValueError("Target path must stay inside the project root") from exc


def normalize_rendered_target(value: str) -> RelativePath:
    return RelativePath(Path(value.strip()))


def defaults_for(target_relative_path: RelativePath) -> dict[str, str]:
    target = target_context_for(target_relative_path)
    return {
        "target_path": target["path"],
        "target_name": target["name"],
        "target_class": target["class"],
        "target_pascal": target["pascal"],
        "target_camel": target["camel"],
        "target_variable": target["variable"],
        "target_snake": target["snake"],
        "target_kebab": target["kebab"],
        "target_slug": target["slug"],
        "target_parent": target["parent"],
    }


def parse_variables(values: tuple[str, ...]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for raw_value in values:
        if "=" not in raw_value:
            raise ValueError(f"Recipe variables must use key=value syntax: {raw_value}")
        name, value = raw_value.split("=", 1)
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Recipe variable names must not be empty")
        variables[normalized_name] = value
    return variables
