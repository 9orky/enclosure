from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, TypedDict

from pydantic import Field, field_validator

from enclosure.shared import config, naming

_VARIABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTTED_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_RECIPE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _normalize_relative_path(value: Path | str, label: str) -> Path:
    normalized_value = Path(str(value).strip().replace("\\", "/"))
    if normalized_value.is_absolute():
        raise ValueError(f"{label} must be relative")
    if not normalized_value.parts:
        raise ValueError(f"{label} must not be empty")
    if any(part in {".", ".."} for part in normalized_value.parts):
        raise ValueError(f"{label} must not traverse outside the target root")
    return normalized_value


class RecipeRole(StrEnum):
    CONTAINER = "container"
    ARCHETYPE = "archetype"
    FRAGMENT = "fragment"


class RecipeSlotState(StrEnum):
    ABSENT = "absent"
    FILE = "file"
    PACKAGE = "package"
    SPLIT_FILES = "split-files"
    SPLIT_PACKAGES = "split-packages"


@dataclass(frozen=True)
class RecipeSlotName:
    value: str

    def __post_init__(self) -> None:
        normalized_value = _normalize_relative_path(self.value, "Recipe slot name")
        object.__setattr__(self, "value", normalized_value.as_posix())


@dataclass(frozen=True)
class RecipeSlot:
    name: RecipeSlotName
    state: RecipeSlotState
    files: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        files = tuple(
            _normalize_relative_path(file_path, "Recipe slot file").as_posix()
            for file_path in self.files
        )
        packages = tuple(
            _normalize_relative_path(package_path, "Recipe slot package").as_posix()
            for package_path in self.packages
        )
        if self.state is RecipeSlotState.SPLIT_FILES and not files:
            raise ValueError(f"Recipe slot {self.name.value} must declare files")
        if self.state is RecipeSlotState.SPLIT_PACKAGES and not packages:
            raise ValueError(f"Recipe slot {self.name.value} must declare packages")
        object.__setattr__(self, "files", files)
        object.__setattr__(self, "packages", packages)

    def summary(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "files": self.files,
            "packages": self.packages,
        }


@dataclass(frozen=True)
class RecipeLadder:
    family: str = ""
    rung: str = ""
    slots: tuple[RecipeSlot, ...] = ()
    declared: bool = False

    def __post_init__(self) -> None:
        normalized_family = self.family.strip()
        normalized_rung = self.rung.strip()
        if self.declared and not normalized_family:
            raise ValueError("Recipe ladder family must not be empty")
        if self.declared and not normalized_rung:
            raise ValueError("Recipe ladder rung must not be empty")
        object.__setattr__(self, "family", normalized_family)
        object.__setattr__(self, "rung", normalized_rung)
        object.__setattr__(self, "slots", tuple(self.slots))

    def is_declared(self) -> bool:
        return self.declared

    def summary(self) -> dict[str, Any]:
        if not self.declared:
            return {}
        return {
            "family": self.family,
            "rung": self.rung,
            "slots": {
                slot.name.value: slot.summary()
                for slot in self.slots
            },
        }


@dataclass(frozen=True)
class RelativePath:
    value: Path

    def __post_init__(self) -> None:
        normalized_value = _normalize_relative_path(self.value, "Recipe paths")
        object.__setattr__(self, "value", normalized_value)

    def as_posix(self) -> str:
        return self.value.as_posix()

    def resolve_from(self, root_path: Path) -> Path:
        return root_path / self.value


class RecipeConfig(config.StrictConfigModel):
    skip: tuple[str, ...]
    roles_map: dict[str, str] = Field(default_factory=dict)

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

    @field_validator("roles_map")
    @classmethod
    def normalize_roles_map(cls, values: dict[str, str]) -> dict[str, str]:
        return {
            module_name.strip().replace("\\", "/"): role_name.strip()
            for module_name, role_name in values.items()
            if module_name.strip() and role_name.strip()
        }

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
    role: RecipeRole
    description: str = ""
    ladder: RecipeLadder = field(default_factory=RecipeLadder)
    includes: tuple[str, ...] = ()
    archetypes: tuple[str, ...] = ()
    roles_map: dict[str, str] = field(default_factory=dict)
    inputs: tuple[RecipeInputSpec, ...] = ()
    files: tuple[RecipeFile, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValueError("Recipe names must not be empty")

        name_path = Path(normalized_name)
        if (
            len(name_path.parts) != 1
            or name_path.parts[0] in {".", ".."}
            or not _RECIPE_NAME_PATTERN.match(normalized_name)
        ):
            raise ValueError("Recipe names must be a single folder name")

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "root_path", Path(self.root_path))
        object.__setattr__(self, "includes", tuple(self.includes))
        object.__setattr__(self, "archetypes", tuple(self.archetypes))
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(self, "files", tuple(self.files))

    def is_empty(self) -> bool:
        return len(self.files) == 0 and len(self.includes) == 0


class RenderedFile(TypedDict):
    source_path: Path
    target_path: Path
    relative_path: RelativePath
    content: str


class RecipePreviewStatus(StrEnum):
    CREATE = "create"
    SKIP_EXISTS = "skip_exists"
    SKIP_CONFIG = "skip_config"


@dataclass(frozen=True)
class RecipePreviewFile:
    source_path: Path
    target_path: Path
    relative_path: RelativePath
    status: RecipePreviewStatus
    content: str


class RecipeGenerationReport(TypedDict):
    recipe_name: str
    project_root: Path
    recipe_found: bool
    recipe_empty: bool
    create_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]
    preview_files: tuple[RecipePreviewFile, ...]


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
    role: str
    ladder: dict[str, Any]
    includes: tuple[str, ...]
    archetypes: tuple[str, ...]
    roles_map: dict[str, str]
    inputs: tuple[str, ...]
    files: tuple[str, ...]


@dataclass(frozen=True)
class RecipeDrift:
    module_name: str
    role_name: str
    ladder_family: str = ""
    ladder_rung: str = ""
    missing_files: tuple[str, ...] = ()
    extra_files: tuple[str, ...] = ()

    def has_drift(self) -> bool:
        return bool(self.missing_files or self.extra_files)


@dataclass(frozen=True)
class RecipeDriftReport:
    project_root: Path
    recipe_root: Path
    architecture_root: Path
    modules_checked: int
    drifts: tuple[RecipeDrift, ...] = ()
    violations: tuple[RecipeCheckViolation, ...] = ()

    def passed(self) -> bool:
        return not self.violations and not self.has_drifts()

    def has_drifts(self) -> bool:
        return any(drift.has_drift() for drift in self.drifts)


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
