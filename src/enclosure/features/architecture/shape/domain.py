from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from code_map import CodeMap
from pydantic import field_validator

from enclosure.shared import architecture, config


ImportCrossingType = Literal["module", "symbol"]
ShapeConfigError = config.ConfigError


class ShapeConfig(config.StrictConfigModel):
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
    allow_optional_function_args: bool
    allow_optional_method_args: bool
    allow_optional_class_properties: bool
    allow_imports_aliases: bool
    enforce_joined_imports: bool
    allowed_imports_crossing_types: list[ImportCrossingType]

    @property
    def effective_allowed_imports_crossing_types(self) -> tuple[ImportCrossingType, ...]:
        return tuple(self.allowed_imports_crossing_types)

    @field_validator(
        "max_classes_per_file",
        "max_interfaces_per_file",
        "max_types_per_file",
        "max_abstract_classes_per_file",
        "max_functions_per_file",
        "max_methods_per_class",
        "max_declared_args_per_function",
        "max_declared_args_per_method",
        "max_lines_count_per_function",
        "max_lines_count_per_method",
        "max_lines_count_per_class",
    )
    @classmethod
    def limit_is_disabled_or_non_negative(cls, value: int) -> int:
        if value < -1:
            raise ValueError("limit must be -1 or greater")
        return value

    @field_validator("allowed_imports_crossing_types")
    @classmethod
    def import_crossing_types_are_unique(
        cls,
        value: list[ImportCrossingType],
    ) -> list[ImportCrossingType]:
        if len(value) != len(set(value)):
            raise ValueError("allowed import crossing types must be unique")
        return value


class ShapeConfigOwner(Protocol):
    shape: ShapeConfig


@dataclass(frozen=True)
class ShapeViolation:
    source_id: str
    rule: str
    actual: int
    limit: int
    symbol_kind: str = "file"
    symbol_name: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "rule": self.rule,
            "actual": self.actual,
            "limit": self.limit,
            "symbol_kind": self.symbol_kind,
            "symbol_name": self.symbol_name,
        }


@dataclass(frozen=True)
class ShapeReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    violations: tuple[ShapeViolation, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "violations": [
                violation.to_json_dict() for violation in self.violations
            ],
        }


def evaluate_shape(
    code_map: CodeMap,
    config: ShapeConfigOwner,
) -> tuple[ShapeViolation, ...]:
    shape = config.shape
    violations: list[ShapeViolation] = []
    for source_id, source_file in sorted(code_map.extraction_result.files.items()):
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_classes_per_file",
            actual=len(source_file.classes),
            limit=shape.max_classes_per_file,
            symbol_kind="file",
            symbol_name="",
        )
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_interfaces_per_file",
            actual=len(source_file.interfaces),
            limit=shape.max_interfaces_per_file,
            symbol_kind="file",
            symbol_name="",
        )
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_types_per_file",
            actual=len(source_file.types),
            limit=shape.max_types_per_file,
            symbol_kind="file",
            symbol_name="",
        )
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_abstract_classes_per_file",
            actual=len(source_file.abstract_classes),
            limit=shape.max_abstract_classes_per_file,
            symbol_kind="file",
            symbol_name="",
        )
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_functions_per_file",
            actual=len(source_file.functions),
            limit=shape.max_functions_per_file,
            symbol_kind="file",
            symbol_name="",
        )
        allowed_import_crossing_types = set(
            shape.effective_allowed_imports_crossing_types
        )
        reported_aliased_imports: set[tuple[str, str]] = set()
        reported_imports: set[tuple[str, str, str]] = set()
        for source_import in source_file.imports:
            if source_import.file_barrier_crossed and (
                source_import.is_aliased and not shape.allow_imports_aliases
            ):
                violation_key = (source_id, source_import.normalized_path)
                if violation_key not in reported_aliased_imports:
                    reported_aliased_imports.add(violation_key)
                    violations.append(
                        ShapeViolation(
                            source_id=source_id,
                            rule="allow_imports_aliases",
                            actual=1,
                            limit=0,
                            symbol_kind="import",
                            symbol_name=source_import.normalized_path,
                        )
                    )
            if (
                not source_import.file_barrier_crossed
                or source_import.crossing_type in allowed_import_crossing_types
            ):
                continue
            violation_key = (
                source_id,
                source_import.normalized_path,
                source_import.crossing_type,
            )
            if violation_key in reported_imports:
                continue
            reported_imports.add(violation_key)
            symbol_name = (
                f"{source_import.normalized_path} ({source_import.crossing_type})"
            )
            violations.append(
                ShapeViolation(
                    source_id=source_id,
                    rule="allowed_imports_crossing_types",
                    actual=1,
                    limit=0,
                    symbol_kind="import",
                    symbol_name=symbol_name,
                )
            )
        if shape.enforce_joined_imports:
            _add_joined_import_violations(
                violations,
                source_id=source_id,
                source_imports=source_file.imports,
            )

        for function in source_file.functions:
            _add_limited_violation(
                violations,
                source_id=source_id,
                rule="max_declared_args_per_function",
                actual=function.declared_args,
                limit=shape.max_declared_args_per_function,
                symbol_kind="function",
                symbol_name=function.name,
            )
            _add_limited_violation(
                violations,
                source_id=source_id,
                rule="max_lines_count_per_function",
                actual=function.line_count,
                limit=shape.max_lines_count_per_function,
                symbol_kind="function",
                symbol_name=function.name,
            )
            if not shape.allow_optional_function_args and function.optional_args > 0:
                violations.append(
                    ShapeViolation(
                        source_id=source_id,
                        rule="allow_optional_function_args",
                        actual=function.optional_args,
                        limit=0,
                        symbol_kind="function",
                        symbol_name=function.name,
                    )
                )

        for class_definition in source_file.classes:
            _add_class_like_violations(
                violations,
                source_id=source_id,
                shape=shape,
                symbol_kind="class",
                symbol_name=class_definition.name,
                methods=class_definition.methods,
                properties=class_definition.properties,
                line_count=class_definition.line_count,
            )

        for abstract_class in source_file.abstract_classes:
            _add_class_like_violations(
                violations,
                source_id=source_id,
                shape=shape,
                symbol_kind="abstract_class",
                symbol_name=abstract_class.name,
                methods=[
                    *abstract_class.abstract_methods,
                    *abstract_class.concrete_methods,
                ],
                properties=abstract_class.properties,
                line_count=abstract_class.line_count,
            )

    return tuple(violations)


def _add_joined_import_violations(
    violations: list[ShapeViolation],
    *,
    source_id: str,
    source_imports,
) -> None:
    imports_by_join_key = {}
    for source_import in source_imports:
        if not source_import.file_barrier_crossed or not source_import.join_key:
            continue
        imports_by_join_key.setdefault(source_import.join_key, []).append(source_import)

    for join_key, imports in sorted(imports_by_join_key.items()):
        if len(imports) <= 1:
            continue
        statement_ids = {
            source_import.statement_id
            for source_import in imports
            if source_import.statement_id
        }
        statement_count = len(statement_ids) if statement_ids else len(imports)
        uses_joined_import = all(
            source_import.uses_joined_import for source_import in imports
        )
        if statement_count <= 1 and uses_joined_import:
            continue
        violations.append(
            ShapeViolation(
                source_id=source_id,
                rule="enforce_joined_imports",
                actual=statement_count if statement_count > 1 else len(imports),
                limit=1,
                symbol_kind="import",
                symbol_name=join_key,
            )
        )


def _add_class_like_violations(
    violations: list[ShapeViolation],
    *,
    source_id: str,
    shape: ShapeConfig,
    symbol_kind: str,
    symbol_name: str,
    methods,
    properties,
    line_count: int,
) -> None:
    _add_limited_violation(
        violations,
        source_id=source_id,
        rule="max_methods_per_class",
        actual=len(methods),
        limit=shape.max_methods_per_class,
        symbol_kind=symbol_kind,
        symbol_name=symbol_name,
    )
    _add_limited_violation(
        violations,
        source_id=source_id,
        rule="max_lines_count_per_class",
        actual=line_count,
        limit=shape.max_lines_count_per_class,
        symbol_kind=symbol_kind,
        symbol_name=symbol_name,
    )
    optional_property_count = sum(
        1
        for property_definition in properties
        if property_definition.is_optional
    )
    if not shape.allow_optional_class_properties and optional_property_count > 0:
        violations.append(
            ShapeViolation(
                source_id=source_id,
                rule="allow_optional_class_properties",
                actual=optional_property_count,
                limit=0,
                symbol_kind=symbol_kind,
                symbol_name=symbol_name,
            )
        )
    for method in methods:
        method_name = f"{symbol_name}.{method.name}"
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_declared_args_per_method",
            actual=method.declared_args,
            limit=shape.max_declared_args_per_method,
            symbol_kind="method",
            symbol_name=method_name,
        )
        _add_limited_violation(
            violations,
            source_id=source_id,
            rule="max_lines_count_per_method",
            actual=method.line_count,
            limit=shape.max_lines_count_per_method,
            symbol_kind="method",
            symbol_name=method_name,
        )
        if not shape.allow_optional_method_args and method.optional_args > 0:
            violations.append(
                ShapeViolation(
                    source_id=source_id,
                    rule="allow_optional_method_args",
                    actual=method.optional_args,
                    limit=0,
                    symbol_kind="method",
                    symbol_name=method_name,
                )
            )


def _add_limited_violation(
    violations: list[ShapeViolation],
    *,
    source_id: str,
    rule: str,
    actual: int,
    limit: int,
    symbol_kind: str,
    symbol_name: str,
) -> None:
    if limit == -1 or actual <= limit:
        return
    violations.append(
        ShapeViolation(
            source_id=source_id,
            rule=rule,
            actual=actual,
            limit=limit,
            symbol_kind=symbol_kind,
            symbol_name=symbol_name,
        )
    )


__all__ = [
    "evaluate_shape",
    "ShapeConfig",
    "ShapeConfigError",
    "ShapeConfigOwner",
    "ShapeReport",
    "ShapeViolation",
]
