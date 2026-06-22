from __future__ import annotations

import copy
import unittest
from importlib.resources import files
from pathlib import Path

import yaml

from enclosure.features.architecture import config as contract_config
from enclosure.features.workspace import config as workspace_config
from enclosure.features.workspace.recipe import domain as recipe_domain
from enclosure.shared import config


class NestedConfigTest(unittest.TestCase):
    def test_packaged_nested_config_loads(self) -> None:
        raw_data = _packaged_config_with_extractor()

        contract_settings = contract_config.ArchitectureConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )
        workspace_settings = workspace_config.WorkspaceConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )

        self.assertEqual("python", contract_settings.language)
        self.assertEqual(".", contract_settings.root)
        self.assertEqual(20, contract_settings.map.top)
        self.assertEqual(10, contract_settings.pressure.top)
        self.assertEqual(5, contract_settings.clusters.group_depth)
        self.assertEqual(20, contract_settings.clusters.top)
        self.assertEqual(5, contract_settings.clusters.files_top)
        self.assertEqual(5, contract_settings.health.top)
        self.assertEqual(
            (),
            workspace_settings.recipe.skip,
        )
        self.assertEqual({}, workspace_settings.recipe.roles_map)
        self.assertEqual(
            raw_data["workspace"]["guidance"]["max_template_chars"],
            workspace_settings.guidance.max_template_chars,
        )
        self.assertEqual(
            raw_data["workspace"]["rules"]["local"]["max_content_chars"],
            workspace_settings.rules.local.max_content_chars,
        )

    def test_missing_required_module_section_fails(self) -> None:
        raw_data = _packaged_config_with_extractor()
        del raw_data["architecture"]["shape"]

        with self.assertRaises(config.ConfigError):
            contract_config.ArchitectureConfig.validate_mapping(
                raw_data,
                Path("enclosure.yaml"),
            )

    def test_missing_required_config_value_fails(self) -> None:
        raw_data = _packaged_config_with_extractor()
        del raw_data["architecture"]["shape"]["max_classes_per_file"]

        with self.assertRaises(config.ConfigError):
            contract_config.ArchitectureConfig.validate_mapping(
                raw_data,
                Path("enclosure.yaml"),
            )

    def test_missing_required_module_default_fails(self) -> None:
        raw_data = _packaged_config_with_extractor()
        del raw_data["architecture"]["map"]["top"]

        with self.assertRaises(config.ConfigError):
            contract_config.ArchitectureConfig.validate_mapping(
                raw_data,
                Path("enclosure.yaml"),
            )

    def test_non_mapping_section_fails(self) -> None:
        raw_data = _packaged_config_with_extractor()
        raw_data["workspace"]["recipe"] = []

        with self.assertRaisesRegex(
            config.ConfigError,
            "workspace.recipe must be a mapping",
        ):
            config.section(
                raw_data,
                "workspace.recipe",
                recipe_domain.RecipeConfig,
                Path("enclosure.yaml"),
            )

    def test_unknown_section_keys_fail(self) -> None:
        raw_data = _packaged_config_with_extractor()
        raw_data["workspace"]["recipe"]["unknown"] = True

        with self.assertRaises(config.ConfigError):
            config.section(
                raw_data,
                "workspace.recipe",
                recipe_domain.RecipeConfig,
                Path("enclosure.yaml"),
            )

    def test_packaged_values_are_the_config_defaults(self) -> None:
        raw_data = _packaged_config_with_extractor()

        contract_settings = contract_config.ArchitectureConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )
        workspace_settings = workspace_config.WorkspaceConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )

        self.assertEqual(-1, contract_settings.shape.max_classes_per_file)
        self.assertEqual(-1, contract_settings.shape.max_interfaces_per_file)
        self.assertEqual(-1, contract_settings.shape.max_types_per_file)
        self.assertEqual(-1, contract_settings.shape.max_abstract_classes_per_file)
        self.assertTrue(contract_settings.shape.allow_optional_function_args)
        self.assertEqual(("module", "symbol"), tuple(
            contract_settings.shape.allowed_imports_crossing_types
        ))
        self.assertEqual(20, contract_settings.map.top)
        self.assertEqual(10, contract_settings.pressure.top)
        self.assertEqual(5, contract_settings.clusters.group_depth)
        self.assertEqual(20, contract_settings.clusters.top)
        self.assertEqual(5, contract_settings.clusters.files_top)
        self.assertEqual(5, contract_settings.health.top)
        self.assertEqual((), workspace_settings.recipe.skip)
        self.assertEqual({}, workspace_settings.recipe.roles_map)
        self.assertEqual(
            raw_data["workspace"]["guidance"]["max_template_chars"],
            workspace_settings.guidance.max_template_chars,
        )
        self.assertEqual(
            raw_data["workspace"]["rules"]["local"]["max_content_chars"],
            workspace_settings.rules.local.max_content_chars,
        )

    def test_guidance_template_limit_allows_disabled_value(self) -> None:
        raw_data = _packaged_config_with_extractor()
        raw_data["workspace"]["guidance"]["max_template_chars"] = -1

        workspace_settings = workspace_config.WorkspaceConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )

        self.assertEqual(-1, workspace_settings.guidance.max_template_chars)

    def test_guidance_template_limit_rejects_values_less_than_disabled(self) -> None:
        raw_data = _packaged_config_with_extractor()
        raw_data["workspace"]["guidance"]["max_template_chars"] = -2

        with self.assertRaises(config.ConfigError):
            workspace_config.WorkspaceConfig.validate_mapping(
                raw_data,
                Path("enclosure.yaml"),
            )

    def test_contract_report_limits_allow_zero_and_unlimited(self) -> None:
        raw_data = _packaged_config_with_extractor()
        raw_data["architecture"]["map"]["top"] = -1
        raw_data["architecture"]["pressure"]["top"] = -1
        raw_data["architecture"]["clusters"]["top"] = 0
        raw_data["architecture"]["clusters"]["files_top"] = -1
        raw_data["architecture"]["health"]["top"] = 0

        contract_settings = contract_config.ArchitectureConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )

        self.assertEqual(-1, contract_settings.map.top)
        self.assertEqual(-1, contract_settings.pressure.top)
        self.assertEqual(0, contract_settings.clusters.top)
        self.assertEqual(-1, contract_settings.clusters.files_top)
        self.assertEqual(0, contract_settings.health.top)

    def test_contract_report_limits_reject_values_less_than_unlimited(self) -> None:
        raw_data = _packaged_config_with_extractor()
        raw_data["architecture"]["map"]["top"] = -2

        with self.assertRaises(config.ConfigError):
            contract_config.ArchitectureConfig.validate_mapping(
                raw_data,
                Path("enclosure.yaml"),
            )

    def test_contract_adapter_properties_support_code_map_contract(self) -> None:
        raw_data = _packaged_config_with_extractor()
        contract_settings = contract_config.ArchitectureConfig.validate_mapping(
            raw_data,
            Path("enclosure.yaml"),
        )

        self.assertEqual(
            contract_settings.root,
            contract_settings.architecture_root,
        )
        self.assertIs(contract_settings.boundaries, contract_settings.rules)
        self.assertEqual([], contract_settings.rules.boundaries)
        self.assertEqual([], contract_settings.rules.tags)


def _packaged_config() -> dict[str, object]:
    raw_text = files("enclosure").joinpath("resources", "enclosure.yaml").read_text(
        encoding="utf-8"
    )
    raw_data = yaml.safe_load(raw_text)
    if not isinstance(raw_data, dict):
        raise AssertionError("Packaged enclosure.yaml must contain a mapping")
    return copy.deepcopy(raw_data)


def _packaged_config_with_extractor() -> dict[str, object]:
    raw_data = _packaged_config()
    raw_data["architecture"]["language"] = "python"
    return raw_data


if __name__ == "__main__":
    unittest.main()
