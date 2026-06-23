from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import modwire
from modwire.shape.rules import FileCountRule, SymbolShapeRule

from enclosure.shared import architecture


@dataclass(frozen=True)
class ShapeViolation:
    source_id: str
    rule: str
    actual: int | str | bool
    limit: int | str | bool
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
    code_map: modwire.CodeMap,
    config: object,
) -> tuple[ShapeViolation, ...]:
    shape = config.shape
    owners = _symbol_owners(code_map)
    violations = [
        normalized
        for violation in modwire.evaluate_shape(
            code_map,
            _modwire_shape_config(shape),
            rules=(FileCountRule(), SymbolShapeRule()),
        )
        if (normalized := _normalize_violation(violation, shape, owners)) is not None
    ]
    violations.extend(_import_violations(code_map, shape))
    if shape.enforce_joined_imports:
        violations.extend(_joined_import_violations(code_map))
    return tuple(violations)


def _modwire_shape_config(shape: object) -> modwire.ShapeConfig:
    return modwire.ShapeConfig(
        max_classes_per_file=shape.max_classes_per_file,
        max_interfaces_per_file=shape.max_interfaces_per_file,
        max_types_per_file=shape.max_types_per_file,
        max_abstract_classes_per_file=shape.max_abstract_classes_per_file,
        max_functions_per_file=shape.max_functions_per_file,
        max_methods_per_class=shape.max_methods_per_class,
        max_declared_args=_combined_limit(
            shape.max_declared_args_per_function,
            shape.max_declared_args_per_method,
        ),
        max_function_lines=shape.max_lines_count_per_function,
        max_method_lines=shape.max_lines_count_per_method,
        max_class_lines=shape.max_lines_count_per_class,
        allow_optional_function_args=shape.allow_optional_function_args,
        allow_optional_method_args=shape.allow_optional_method_args,
        allow_optional_class_properties=shape.allow_optional_class_properties,
        allow_import_aliases=shape.allow_imports_aliases,
        allowed_import_crossing_types=tuple(shape.allowed_imports_crossing_types),
        require_joined_imports=False,
    )


def _combined_limit(function_limit: int, method_limit: int) -> int:
    if function_limit == method_limit:
        return function_limit
    if function_limit == -1:
        return method_limit
    if method_limit == -1:
        return function_limit
    return max(function_limit, method_limit)


def _normalize_violation(
    violation: object,
    shape: object,
    owners: dict[tuple[str, str, str], tuple[str, str]],
) -> ShapeViolation | None:
    rule_name = getattr(violation, "rule_name")
    source_id = getattr(violation, "source_id")
    symbol_kind = getattr(violation, "symbol_kind") or "file"
    symbol_name = getattr(violation, "symbol_name") or ""
    actual = getattr(violation, "actual")
    limit = getattr(violation, "limit")

    if rule_name == "max_declared_args":
        if symbol_kind == "function":
            rule_name = "max_declared_args_per_function"
            limit = shape.max_declared_args_per_function
        else:
            rule_name = "max_declared_args_per_method"
            limit = shape.max_declared_args_per_method
        if limit == -1 or actual <= limit:
            return None
    elif rule_name == "max_function_lines":
        rule_name = "max_lines_count_per_function"
    elif rule_name == "max_method_lines":
        rule_name = "max_lines_count_per_method"
    elif rule_name == "max_class_lines":
        rule_name = "max_lines_count_per_class"
    elif rule_name == "allow_import_aliases":
        rule_name = "allow_imports_aliases"
        actual, limit = 1, 0
    elif rule_name == "allowed_import_crossing_types":
        symbol_name = f"{symbol_name} ({actual})"
        actual, limit = 1, 0

    owner = owners.get((source_id, symbol_kind, symbol_name))
    if owner is not None:
        symbol_kind, symbol_name = owner

    return ShapeViolation(
        source_id=source_id,
        rule=rule_name,
        actual=actual,
        limit=limit,
        symbol_kind=symbol_kind,
        symbol_name=symbol_name,
    )


def _symbol_owners(
    code_map: modwire.CodeMap,
) -> dict[tuple[str, str, str], tuple[str, str]]:
    owners: dict[tuple[str, str, str], tuple[str, str]] = {}
    for source_id, source_file in code_map.extraction_result.files.items():
        for class_definition in source_file.classes:
            _add_class_owners(owners, source_id, "class", class_definition)
        for abstract_class in source_file.abstract_classes:
            _add_abstract_class_owners(owners, source_id, abstract_class)
    return owners


def _add_class_owners(
    owners: dict[tuple[str, str, str], tuple[str, str]],
    source_id: str,
    owner_kind: str,
    class_definition: object,
) -> None:
    for method in getattr(class_definition, "methods", ()):
        owners[(source_id, "method", method.name)] = (
            "method",
            f"{class_definition.name}.{method.name}",
        )
    for property_definition in getattr(class_definition, "properties", ()):
        owners[(source_id, f"{owner_kind}_property", property_definition.name)] = (
            owner_kind,
            class_definition.name,
        )


def _add_abstract_class_owners(
    owners: dict[tuple[str, str, str], tuple[str, str]],
    source_id: str,
    abstract_class: object,
) -> None:
    for method in (
        *getattr(abstract_class, "abstract_methods", ()),
        *getattr(abstract_class, "concrete_methods", ()),
    ):
        owners[(source_id, "method", method.name)] = (
            "method",
            f"{abstract_class.name}.{method.name}",
        )
    for property_definition in getattr(abstract_class, "properties", ()):
        owners[(source_id, "abstract_class_property", property_definition.name)] = (
            "abstract_class",
            abstract_class.name,
        )


def _import_violations(
    code_map: modwire.CodeMap,
    shape: object,
) -> tuple[ShapeViolation, ...]:
    violations: list[ShapeViolation] = []
    allowed_import_crossing_types = set(shape.allowed_imports_crossing_types)
    for source_id, source_file in code_map.extraction_result.files.items():
        reported_aliased_imports: set[tuple[str, str]] = set()
        reported_imports: set[tuple[str, str, str]] = set()
        for source_import in source_file.imports:
            if source_import.is_aliased and not shape.allow_imports_aliases:
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
            if not source_import.file_barrier_crossed:
                continue
            if source_import.crossing_type in allowed_import_crossing_types:
                continue
            violation_key = (
                source_id,
                source_import.normalized_path,
                source_import.crossing_type,
            )
            if violation_key in reported_imports:
                continue
            reported_imports.add(violation_key)
            violations.append(
                ShapeViolation(
                    source_id=source_id,
                    rule="allowed_imports_crossing_types",
                    actual=1,
                    limit=0,
                    symbol_kind="import",
                    symbol_name=(
                        f"{source_import.normalized_path} "
                        f"({source_import.crossing_type})"
                    ),
                )
            )
    return tuple(violations)


def _joined_import_violations(
    code_map: modwire.CodeMap,
) -> tuple[ShapeViolation, ...]:
    violations: list[ShapeViolation] = []
    for source_id, source_file in code_map.extraction_result.files.items():
        imports_by_join_key = {}
        for source_import in source_file.imports:
            join_key = source_import.join_key or source_import.normalized_path
            if not join_key:
                continue
            imports_by_join_key.setdefault(join_key, []).append(source_import)
        for join_key, imports in sorted(imports_by_join_key.items()):
            if len(imports) <= 1:
                continue
            statement_ids = {
                source_import.statement_id
                for source_import in imports
                if source_import.statement_id
            }
            statement_count = len(statement_ids) if statement_ids else len(imports)
            if statement_count <= 1 and all(
                source_import.uses_joined_import for source_import in imports
            ):
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
    return tuple(violations)


__all__ = [
    "evaluate_shape",
    "ShapeReport",
    "ShapeViolation",
]
