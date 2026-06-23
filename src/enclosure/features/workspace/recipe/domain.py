from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, TypedDict

from enclosure.shared.scaffolding import scaffolding


@dataclass(frozen=True)
class RecipeCommandContext:
    project_root: Path
    recipe_root: Path


@dataclass(frozen=True)
class RecipeGenerationConfig:
    skip: tuple[str, ...] = ()
    roles_map: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "skip",
            tuple(
                value.strip().replace("\\", "/")
                for value in self.skip
                if value.strip()
            ),
        )
        object.__setattr__(
            self,
            "roles_map",
            {
                module_name.strip().replace("\\", "/"): role_name.strip()
                for module_name, role_name in self.roles_map.items()
                if module_name.strip() and role_name.strip()
            },
        )

    @property
    def skip_globs(self) -> tuple[str, ...]:
        return self.skip

    def should_skip(self, relative_path: Path | str) -> bool:
        relative_path_text = Path(relative_path).as_posix()
        return any(fnmatch(relative_path_text, pattern) for pattern in self.skip)

    @classmethod
    def from_config(cls, value: object) -> RecipeGenerationConfig:
        roles_map = getattr(value, "roles_map", {})
        if not isinstance(roles_map, dict):
            roles_map = vars(roles_map)
        return cls(
            skip=tuple(getattr(value, "skip", ())),
            roles_map=dict(roles_map),
        )


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


class RecipePreviewStatus(StrEnum):
    CREATE = "create"
    SKIP_EXISTS = "skip_exists"
    SKIP_CONFIG = "skip_config"


@dataclass(frozen=True)
class RecipePreviewFile:
    source_path: Path
    target_path: Path
    relative_path: Path
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


@dataclass(frozen=True)
class RecipeBenchFileContent:
    path: str
    content: str
    truncated: bool = False


@dataclass(frozen=True)
class RecipeBenchContentWeight:
    path: str
    line_count: int
    symbol_count: int
    reason: str


@dataclass(frozen=True)
class RecipeBenchModule:
    module_name: str
    actual_files: tuple[str, ...] = ()
    expected_files: tuple[str, ...] = ()
    residue_files: tuple[str, ...] = ()
    slot_growth_files: tuple[str, ...] = ()
    content_weights: tuple[RecipeBenchContentWeight, ...] = ()
    missing_files: tuple[str, ...] = ()
    file_contents: tuple[RecipeBenchFileContent, ...] = ()

    def has_residue(self) -> bool:
        return bool(self.residue_files)

    def has_warp(self) -> bool:
        return bool(
            self.missing_files
            or self.residue_files
            or self.slot_growth_files
            or self.content_weights
        )


@dataclass(frozen=True)
class RecipeBenchRecurrence:
    path: str
    count: int
    modules: tuple[str, ...]
    label: str


@dataclass(frozen=True)
class RecipeBenchReport:
    project_root: Path
    recipe_root: Path
    architecture_root: Path
    selected_module: str
    role_name: str
    classification: str
    same_role_modules: tuple[RecipeBenchModule, ...] = ()
    recurrence: tuple[RecipeBenchRecurrence, ...] = ()
    slot_growth_recurrence: tuple[RecipeBenchRecurrence, ...] = ()
    content_weight_recurrence: tuple[RecipeBenchRecurrence, ...] = ()
    selected: RecipeBenchModule | None = None
    violations: tuple[RecipeCheckViolation, ...] = ()

    def passed(self) -> bool:
        return not self.violations

    @property
    def same_role_module_count(self) -> int:
        return len(self.same_role_modules)

    @property
    def local_residue_count(self) -> int:
        if self.selected is None:
            return 0
        return len(self.selected.residue_files)

    @property
    def local_slot_growth_count(self) -> int:
        if self.selected is None:
            return 0
        return len(self.selected.slot_growth_files)

    @property
    def local_content_weight_count(self) -> int:
        if self.selected is None:
            return 0
        return len(self.selected.content_weights)

    @property
    def local_warp_count(self) -> int:
        if self.selected is None:
            return 0
        return (
            len(self.selected.missing_files)
            + len(self.selected.residue_files)
            + len(self.selected.slot_growth_files)
            + len(self.selected.content_weights)
        )

    @property
    def repeated_residue_count(self) -> int:
        if self.selected is None:
            return 0
        repeated_paths = {
            item.path
            for item in self.recurrence
            if item.count > 1
        }
        return sum(1 for path in self.selected.residue_files if path in repeated_paths)

    @property
    def repeated_slot_growth_count(self) -> int:
        if self.selected is None:
            return 0
        repeated_paths = {
            item.path
            for item in self.slot_growth_recurrence
            if item.count > 1
        }
        return sum(
            1
            for path in self.selected.slot_growth_files
            if path in repeated_paths
        )

    @property
    def repeated_content_weight_count(self) -> int:
        if self.selected is None:
            return 0
        repeated_paths = {
            item.path
            for item in self.content_weight_recurrence
            if item.count > 1
        }
        return sum(
            1
            for weight in self.selected.content_weights
            if weight.path in repeated_paths
        )

    @property
    def repeated_warp_count(self) -> int:
        return (
            self.repeated_residue_count
            + self.repeated_slot_growth_count
            + self.repeated_content_weight_count
        )


@dataclass(frozen=True)
class RecipeBenchAllReport:
    project_root: Path
    recipe_root: Path
    architecture_root: Path
    classification: str
    reports: tuple[RecipeBenchReport, ...] = ()
    violations: tuple[RecipeCheckViolation, ...] = ()

    def passed(self) -> bool:
        return not self.violations and all(report.passed() for report in self.reports)

    @property
    def module_count(self) -> int:
        return len(self.reports)

    @property
    def role_count(self) -> int:
        return len({report.role_name for report in self.reports if report.role_name})

    @property
    def local_residue_count(self) -> int:
        return sum(report.local_residue_count for report in self.reports)

    @property
    def local_slot_growth_count(self) -> int:
        return sum(report.local_slot_growth_count for report in self.reports)

    @property
    def local_content_weight_count(self) -> int:
        return sum(report.local_content_weight_count for report in self.reports)

    @property
    def local_warp_count(self) -> int:
        return sum(report.local_warp_count for report in self.reports)

    @property
    def repeated_residue_count(self) -> int:
        return sum(report.repeated_residue_count for report in self.reports)

    @property
    def repeated_slot_growth_count(self) -> int:
        return sum(report.repeated_slot_growth_count for report in self.reports)

    @property
    def repeated_content_weight_count(self) -> int:
        return sum(report.repeated_content_weight_count for report in self.reports)

    @property
    def repeated_warp_count(self) -> int:
        return sum(report.repeated_warp_count for report in self.reports)

    @property
    def reports_with_residue_count(self) -> int:
        return sum(1 for report in self.reports if report.local_residue_count)

    @property
    def reports_with_warp_count(self) -> int:
        return sum(1 for report in self.reports if report.local_warp_count)


parse_variables = scaffolding.parse_variables
