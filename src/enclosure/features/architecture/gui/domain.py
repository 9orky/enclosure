from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuiSymbol:
    kind: str
    name: str
    line_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "name": self.name,
            "line_count": self.line_count,
        }


@dataclass(frozen=True)
class GuiFile:
    source_id: str
    module_name: str
    layer_name: str
    symbols: tuple[GuiSymbol, ...]
    imports: tuple[str, ...]
    boundary_findings: tuple[dict[str, object], ...]
    shape_findings: tuple[dict[str, object], ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "module_name": self.module_name,
            "layer_name": self.layer_name,
            "symbols": [symbol.to_json_dict() for symbol in self.symbols],
            "imports": list(self.imports),
            "boundary_findings": list(self.boundary_findings),
            "shape_findings": list(self.shape_findings),
        }


@dataclass(frozen=True)
class GuiTag:
    name: str
    match: str
    excluded_patterns: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "match": self.match,
            "excluded_patterns": list(self.excluded_patterns),
        }


@dataclass(frozen=True)
class GuiBoundaryRule:
    source: str
    disallow: tuple[str, ...]
    allow: tuple[str, ...]
    allow_same_match: bool

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "disallow": list(self.disallow),
            "allow": list(self.allow),
            "allow_same_match": self.allow_same_match,
        }


@dataclass(frozen=True)
class GuiShapeConfig:
    max_classes_per_file: int
    max_interfaces_per_file: int
    max_types_per_file: int
    max_abstract_classes_per_file: int
    max_functions_per_file: int
    max_methods_per_class: int
    max_declared_args_per_function: int
    max_declared_args_per_method: int
    max_lines_count_per_function: int
    max_lines_count_per_method: int
    max_lines_count_per_class: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "max_classes_per_file": self.max_classes_per_file,
            "max_interfaces_per_file": self.max_interfaces_per_file,
            "max_types_per_file": self.max_types_per_file,
            "max_abstract_classes_per_file": self.max_abstract_classes_per_file,
            "max_functions_per_file": self.max_functions_per_file,
            "max_methods_per_class": self.max_methods_per_class,
            "max_declared_args_per_function": self.max_declared_args_per_function,
            "max_declared_args_per_method": self.max_declared_args_per_method,
            "max_lines_count_per_function": self.max_lines_count_per_function,
            "max_lines_count_per_method": self.max_lines_count_per_method,
            "max_lines_count_per_class": self.max_lines_count_per_class,
        }


@dataclass(frozen=True)
class GuiSnapshot:
    project_root: Path
    architecture_root: str
    config_path: Path
    files_checked: int
    files_excluded: int
    files: tuple[GuiFile, ...]
    tags: tuple[GuiTag, ...]
    boundary_rules: tuple[GuiBoundaryRule, ...]
    flow_layers: tuple[str, ...]
    exclusions: tuple[str, ...]
    shape_config: GuiShapeConfig
    dependencies: tuple[dict[str, object], ...]
    hotspots: tuple[dict[str, object], ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "architecture_root": self.architecture_root,
            "config_path": str(self.config_path),
            "files_checked": self.files_checked,
            "files_excluded": self.files_excluded,
            "files": [file.to_json_dict() for file in self.files],
            "tags": [tag.to_json_dict() for tag in self.tags],
            "boundary_rules": [rule.to_json_dict() for rule in self.boundary_rules],
            "flow_layers": list(self.flow_layers),
            "exclusions": list(self.exclusions),
            "shape_config": self.shape_config.to_json_dict(),
            "dependencies": list(self.dependencies),
            "hotspots": list(self.hotspots),
        }


__all__ = [
    "GuiBoundaryRule",
    "GuiFile",
    "GuiShapeConfig",
    "GuiSnapshot",
    "GuiSymbol",
    "GuiTag",
]
