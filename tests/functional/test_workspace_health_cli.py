from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_workspace_health_reports_missing_rules_and_recipes(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "health")

    assert result.returncode == 1
    assert "Workspace Health:" in result.stdout
    assert "- Paths: target present, rules missing" in result.stdout
    assert "Workspace rules directory not found" in result.stdout
    assert "recipe templates - 2 violation(s) detected" in result.stdout


def test_workspace_health_reports_recipe_mapping_without_recipe_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    result = run_cli(project_root, "workspace", "health")

    assert result.returncode == 1
    assert "Recipes: 2 checked" in result.stdout
    assert "0 violation(s)" in result.stdout
    assert "workspace rules - Workspace rules directory not found" in result.stdout
