from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


CONTRACT_PATH = Path(".enclosure/enclosure.yaml")


@pytest.fixture
def configured_recipe_names() -> tuple[str, ...]:
    roles_map = _contract_roles_map()
    recipe_names = {
        recipe_name
        for recipe_group in roles_map.values()
        for recipe_name in recipe_group.split("+")
        if recipe_name
    }
    return tuple(sorted(recipe_names))


@pytest.fixture
def configured_module_names() -> tuple[str, ...]:
    roles_map = _contract_roles_map()
    return tuple(sorted(roles_map))


def _contract_roles_map() -> dict[str, str]:
    contract = _load_contract()
    recipe = contract.get("workspace", {}).get("recipe", {})
    roles_map = recipe.get("roles_map", {})
    if not isinstance(roles_map, dict) or not roles_map:
        raise AssertionError("workspace.recipe.roles_map must contain test subjects")
    return {str(module_name): str(recipe_name) for module_name, recipe_name in roles_map.items()}


def _load_contract() -> dict[str, Any]:
    raw_data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8")) or {}
    if not isinstance(raw_data, dict):
        raise AssertionError(f"Contract must be a mapping: {CONTRACT_PATH}")
    return raw_data
