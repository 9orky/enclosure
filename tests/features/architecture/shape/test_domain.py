from __future__ import annotations

import unittest
from types import SimpleNamespace

from code_map.definitions import SourceFile

from enclosure.features.architecture.shape import domain


class ShapeEvaluationTest(unittest.TestCase):
    def test_new_source_item_file_limits_are_evaluated(self) -> None:
        violations = domain.evaluate_shape(
            _code_map(
                SourceFile.model_validate(
                    {
                        "imports": [],
                        "classes": [],
                        "interfaces": [
                            {
                                "name": "UserPort",
                                "visibility": "public",
                                "visibility_intent": "public",
                                "methods": [],
                                "properties": [],
                                "signatures": [],
                                "line_count": 3,
                            }
                        ],
                        "types": [
                            {
                                "name": "UserPayload",
                                "visibility": "public",
                                "visibility_intent": "public",
                                "properties": [],
                                "signatures": [],
                                "line_count": 2,
                            }
                        ],
                        "abstract_classes": [
                            {
                                "name": "BaseRepository",
                                "visibility": "public",
                                "visibility_intent": "public",
                                "abstract_methods": [],
                                "concrete_methods": [],
                                "properties": [],
                                "line_count": 5,
                            }
                        ],
                        "functions": [],
                        "line_count": 10,
                        "code_line_count": 8,
                        "public_symbol_count": 3,
                    }
                )
            ),
            _config(
                max_interfaces_per_file=0,
                max_types_per_file=0,
                max_abstract_classes_per_file=0,
            ),
        )

        self.assertEqual(
            {violation.rule for violation in violations},
            {
                "max_interfaces_per_file",
                "max_types_per_file",
                "max_abstract_classes_per_file",
            },
        )

    def test_abstract_classes_use_class_like_shape_rules(self) -> None:
        violations = domain.evaluate_shape(
            _code_map(
                SourceFile.model_validate(
                    {
                        "imports": [],
                        "classes": [],
                        "interfaces": [],
                        "types": [],
                        "abstract_classes": [
                            {
                                "name": "BaseRepository",
                                "visibility": "public",
                                "visibility_intent": "public",
                                "abstract_methods": [
                                    {
                                        "name": "load",
                                        "visibility": "public",
                                        "visibility_intent": "public",
                                        "line_count": 1,
                                        "declared_args": 2,
                                        "optional_args": 1,
                                    }
                                ],
                                "concrete_methods": [
                                    {
                                        "name": "save",
                                        "visibility": "public",
                                        "visibility_intent": "public",
                                        "line_count": 1,
                                        "declared_args": 0,
                                        "optional_args": 0,
                                    }
                                ],
                                "properties": [
                                    {"name": "nickname", "is_optional": True}
                                ],
                                "line_count": 20,
                            }
                        ],
                        "functions": [],
                        "line_count": 20,
                        "code_line_count": 15,
                        "public_symbol_count": 1,
                    }
                )
            ),
            _config(
                max_methods_per_class=1,
                max_lines_count_per_class=10,
                max_declared_args_per_method=1,
                allow_optional_method_args=False,
                allow_optional_class_properties=False,
            ),
        )

        self.assertEqual(
            {
                (violation.rule, violation.symbol_kind, violation.symbol_name)
                for violation in violations
            },
            {
                ("max_methods_per_class", "abstract_class", "BaseRepository"),
                ("max_lines_count_per_class", "abstract_class", "BaseRepository"),
                (
                    "allow_optional_class_properties",
                    "abstract_class",
                    "BaseRepository",
                ),
                ("max_declared_args_per_method", "method", "BaseRepository.load"),
                ("allow_optional_method_args", "method", "BaseRepository.load"),
            },
        )


def _code_map(source_file: SourceFile):
    return SimpleNamespace(
        extraction_result=SimpleNamespace(files={"sample": source_file})
    )


def _config(**overrides):
    values = {
        "max_classes_per_file": -1,
        "max_interfaces_per_file": -1,
        "max_types_per_file": -1,
        "max_abstract_classes_per_file": -1,
        "max_functions_per_file": -1,
        "max_methods_per_class": -1,
        "max_declared_args_per_function": -1,
        "max_declared_args_per_method": -1,
        "max_lines_count_per_function": -1,
        "max_lines_count_per_method": -1,
        "max_lines_count_per_class": -1,
        "allow_optional_function_args": True,
        "allow_optional_method_args": True,
        "allow_optional_class_properties": True,
        "allow_imports_aliases": True,
        "enforce_joined_imports": False,
        "allowed_imports_crossing_types": ["module", "symbol"],
    }
    values.update(overrides)
    return SimpleNamespace(shape=domain.ShapeConfig.model_validate(values))


if __name__ == "__main__":
    unittest.main()
