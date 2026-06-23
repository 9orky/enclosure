from __future__ import annotations

from typing import Literal

from modwire import ShapeConfig as ModwireShapeConfig
from pydantic import Field
from pydantic import field_validator

from ..base import StrictConfigModel

ImportCrossingType = Literal["module", "symbol"]


class ShapeConfig(StrictConfigModel):
    max_classes_per_file: int = -1
    max_interfaces_per_file: int = -1
    max_types_per_file: int = -1
    max_abstract_classes_per_file: int = -1
    max_functions_per_file: int = -1
    max_methods_per_class: int = -1
    max_declared_args_per_function: int = -1
    max_declared_args_per_method: int = -1
    max_lines_count_per_function: int = -1
    max_lines_count_per_method: int = -1
    max_lines_count_per_class: int = -1
    allow_optional_function_args: bool = True
    allow_optional_method_args: bool = True
    allow_optional_class_properties: bool = True
    allow_imports_aliases: bool = True
    enforce_joined_imports: bool = False
    allowed_imports_crossing_types: list[ImportCrossingType] = Field(
        default_factory=lambda: ["module", "symbol"]
    )

    def to_modwire_config(self) -> ModwireShapeConfig:
        return ModwireShapeConfig(
            max_classes_per_file=self.max_classes_per_file,
            max_interfaces_per_file=self.max_interfaces_per_file,
            max_types_per_file=self.max_types_per_file,
            max_abstract_classes_per_file=self.max_abstract_classes_per_file,
            max_functions_per_file=self.max_functions_per_file,
            max_methods_per_class=self.max_methods_per_class,
            max_declared_args=_combined_limit(
                self.max_declared_args_per_function,
                self.max_declared_args_per_method,
            ),
            max_function_lines=self.max_lines_count_per_function,
            max_method_lines=self.max_lines_count_per_method,
            max_class_lines=self.max_lines_count_per_class,
            allow_optional_function_args=self.allow_optional_function_args,
            allow_optional_method_args=self.allow_optional_method_args,
            allow_optional_class_properties=self.allow_optional_class_properties,
            allow_import_aliases=self.allow_imports_aliases,
            allowed_import_crossing_types=tuple(self.allowed_imports_crossing_types),
            require_joined_imports=False,
        )

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


def _combined_limit(function_limit: int, method_limit: int) -> int:
    if function_limit == method_limit:
        return function_limit
    if function_limit == -1:
        return method_limit
    if method_limit == -1:
        return function_limit
    return max(function_limit, method_limit)


__all__ = ["ImportCrossingType", "ShapeConfig"]
