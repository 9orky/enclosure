from __future__ import annotations

import copy
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from enclosure.shared.config import ConfigError
from enclosure.shared.config.architecture.shape import ShapeConfig
from enclosure.shared.config.facade import SettingsFacade
from enclosure.shared.config.manifest import Manifest


def test_valid_config_loads_whole_graph_and_exposes_metadata(tmp_path: Path) -> None:
    facade = _settings_for(tmp_path, _valid_manifest())

    loaded = facade.query("architecture")

    assert loaded.root == "src/enclosure/features"
    assert facade.metadata.project_root == tmp_path
    assert facade.metadata.target_dir == tmp_path / ".enclosure"
    assert (
        facade.metadata.canonical_config_path
        == tmp_path / ".enclosure" / "enclosure.yaml"
    )
    assert facade.metadata.recipes_dir == tmp_path / ".enclosure" / "recipes"
    assert facade.metadata.plans_dir == tmp_path / ".enclosure" / "plans"
    assert facade.metadata.cache_dir == tmp_path / ".enclosure" / ".cache"
    assert facade.metadata.dev_dir == tmp_path / ".dev"
    assert facade.metadata.rules_dir == tmp_path / ".enclosure" / "rules"
    assert facade.metadata.local_rules_dir == tmp_path / ".enclosure" / "rules" / "local"
    assert (
        facade.metadata.bootstrap_instruction_path
        == tmp_path / ".github" / "copilot-instructions.md"
    )
    assert facade.metadata.agent_instruction_path == tmp_path / "AGENTS.md"


def test_query_supports_dot_notation_for_scalars_and_objects(
    tmp_path: Path,
) -> None:
    facade = _settings_for(tmp_path, _valid_manifest())

    architecture = facade.query("architecture")
    shape = facade.query("architecture.shape")

    assert architecture.root == "src/enclosure/features"
    assert shape.max_classes_per_file == -1
    assert shape.allowed_imports_crossing_types == ["module"]


def test_query_supports_dot_selected_lists(tmp_path: Path) -> None:
    facade = _settings_for(tmp_path, _valid_manifest())

    tags = facade.query("architecture.boundaries.tags")

    assert len(tags) == 2
    assert tags[0].name == "context"
    assert tags[0].excluded_patterns == ("__init__", "*/*/*")


def test_query_missing_attribute_raises_attribute_error(tmp_path: Path) -> None:
    facade = _settings_for(tmp_path, _valid_manifest())

    with pytest.raises(AttributeError):
        facade.query("architecture.missing")


def test_empty_config_loads_default_graph(tmp_path: Path) -> None:
    facade = _settings_for(tmp_path, {})

    assert facade.query("architecture.language") == "python"
    assert facade.query("architecture.root") == "."
    assert facade.query("architecture.shape.allowed_imports_crossing_types") == [
        "module",
        "symbol",
    ]
    assert facade.query("workspace.rules.local.max_content_chars") == 1200


def test_dump_manifest_returns_validated_graph_yaml_with_aliases(
    tmp_path: Path,
) -> None:
    facade = _settings_for(tmp_path, _valid_manifest())

    dumped = yaml.safe_load(facade.dump_manifest())

    assert dumped["architecture"]["boundaries"]["tags"][0]["except"] == [
        "__init__",
        "*/*/*",
    ]
    assert "except_" not in dumped["architecture"]["boundaries"]["tags"][0]
    assert dumped["workspace"]["recipe"]["skip"] == [
        "**/__pycache__/**",
    ]
    assert dumped["workspace"]["recipe"]["roles_map"] == {
        "architecture/boundaries": "module-report-cli",
    }


def test_manifest_dump_default_comes_from_default_settings_graph() -> None:
    dumped = yaml.safe_load(Manifest.dump_default())

    assert dumped["architecture"]["language"] == "python"
    assert dumped["architecture"]["root"] == "."
    assert dumped["architecture"]["boundaries"]["tags"] == []
    assert dumped["architecture"]["shape"]["allowed_imports_crossing_types"] == [
        "module",
        "symbol",
    ]
    assert dumped["workspace"]["recipe"]["roles_map"] == {}


def test_invalid_yaml_raises_config_error(tmp_path: Path) -> None:
    config_path = _config_path(tmp_path)
    config_path.parent.mkdir()
    config_path.write_text("architecture: [", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid config file syntax"):
        SettingsFacade(Manifest(tmp_path))


def test_non_mapping_yaml_raises_config_error(tmp_path: Path) -> None:
    config_path = _config_path(tmp_path)
    config_path.parent.mkdir()
    config_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="mapping at the top level"):
        SettingsFacade(Manifest(tmp_path))


def test_invalid_nested_values_raise_config_error(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["architecture"]["map"]["top"] = -2

    with pytest.raises(ConfigError, match="architecture.map.top"):
        _settings_for(tmp_path, manifest)


def test_no_partial_facade_is_exposed_after_validation_failure(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["architecture"]["shape"]["max_classes_per_file"] = -2

    with pytest.raises(ConfigError):
        _settings_for(tmp_path, manifest)


def test_facade_does_not_expose_lazy_load_or_manifest_property() -> None:
    assert not hasattr(SettingsFacade, "load")
    assert not hasattr(SettingsFacade, "manifest")


def test_manifest_requires_explicit_project_root() -> None:
    with pytest.raises(TypeError):
        Manifest()


def test_manifest_does_not_search_up_from_project_root(tmp_path: Path) -> None:
    parent_config_path = _config_path(tmp_path)
    parent_config_path.parent.mkdir()
    parent_config_path.write_text(yaml.safe_dump(_valid_manifest()), encoding="utf-8")
    child_root = tmp_path / "child"
    child_root.mkdir()

    with pytest.raises(ConfigError, match="Could not find a configuration file"):
        Manifest(child_root)


def test_shape_config_returns_modwire_config() -> None:
    config = ShapeConfig.model_validate(_valid_manifest()["architecture"]["shape"])

    modwire_config = config.to_modwire_config()

    assert modwire_config.max_classes_per_file == -1
    assert modwire_config.allowed_import_crossing_types == ("module",)


def test_shared_config_package_imports_no_feature_or_other_shared_modules() -> None:
    for module_name in tuple(sys.modules):
        if module_name == "enclosure.shared.config":
            del sys.modules[module_name]
        elif module_name.startswith("enclosure.shared.config."):
            del sys.modules[module_name]

    already_imported = _forbidden_enclosure_modules()

    importlib.import_module("enclosure.shared.config")

    imported = _forbidden_enclosure_modules() - already_imported
    assert imported == set()


def _forbidden_enclosure_modules() -> set[str]:
    return {
        module_name
        for module_name in sys.modules
        if module_name.startswith("enclosure.features.")
        or (
            module_name.startswith("enclosure.shared.")
            and not (
                module_name == "enclosure.shared.config"
                or module_name.startswith("enclosure.shared.config.")
            )
        )
    }


def _settings_for(tmp_path: Path, manifest: dict[str, Any]) -> SettingsFacade:
    config_path = _config_path(tmp_path)
    config_path.parent.mkdir()
    config_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return SettingsFacade(Manifest(tmp_path))


def _config_path(tmp_path: Path) -> Path:
    return tmp_path / ".enclosure" / "enclosure.yaml"


def _valid_manifest() -> dict[str, Any]:
    return copy.deepcopy(
        {
            "architecture": {
                "language": "python",
                "root": "src/enclosure/features",
                "exclusions": [".venv/**", ".enclosure/**"],
                "boundaries": {
                    "tags": [
                        {
                            "name": "context",
                            "match": "*",
                            "except": ["__init__", "*/*/*"],
                            "exclude": [],
                        },
                        {
                            "name": "module",
                            "match": "*/*",
                            "except": ["*/__init__"],
                            "exclude": [],
                        },
                    ],
                    "rules": [
                        {
                            "source": "*",
                            "disallow": ["*"],
                            "allow": ["*/*/__init__"],
                            "allow_same_match": False,
                        }
                    ],
                    "flow": {
                        "layers": ["ui", "application", "infrastructure", "domain"],
                        "realms": [
                            {
                                "name": "module",
                                "module_tag": "module",
                            }
                        ],
                        "analyzers": ["backward-flow"],
                    },
                },
                "shape": {
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
                    "allow_optional_function_args": False,
                    "allow_optional_method_args": False,
                    "allow_optional_class_properties": False,
                    "allow_imports_aliases": False,
                    "enforce_joined_imports": True,
                    "allowed_imports_crossing_types": ["module"],
                },
                "map": {"top": -1},
                "pressure": {"top": 10},
                "clusters": {"group_depth": 5, "top": 20, "files_top": 5},
                "health": {"top": 5},
            },
            "workspace": {
                "guidance": {"max_template_chars": 1200},
                "recipe": {
                    "skip": [" **/__pycache__/** ", ""],
                    "roles_map": {" architecture/boundaries ": " module-report-cli "},
                },
                "rules": {"local": {"max_content_chars": 1200}},
                "sync": {},
            },
        }
    )
