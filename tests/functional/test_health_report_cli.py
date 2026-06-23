from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_root_health_reports_workspace_and_architecture_findings(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "health", "--top", "-1")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "Enclosure Health:" in result.stdout
    assert "- Paths: target present, rules missing, recipes missing" in result.stdout
    assert "- Boundaries: 2 violation(s)" in result.stdout
    assert "- Shape: 1 violation(s)" in result.stdout
    assert "workspace/rules" in result.stdout
    assert "architecture/boundaries" in result.stdout
    assert "architecture/shape" in result.stdout


def test_root_health_summary_aggregates_workspace_and_architecture_counts(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "health", "--v")

    assert result.returncode == 1
    assert "Enclosure Health (summary):" in result.stdout
    assert "Workspace:" in result.stdout
    assert "Architecture:" in result.stdout
    assert "- Boundary violations: 2" in result.stdout
    assert "- Shape violations: 1" in result.stdout


def test_root_health_reports_stress_architecture_and_workspace_findings(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "health", "--top", "-1")

    assert result.returncode == 1
    assert "- Rules: unknown checked, unknown with issue(s)" in result.stdout
    assert "- Boundaries: 4 violation(s)" in result.stdout
    assert "- Shape: 11 violation(s)" in result.stdout
    assert "- Map: 2 module(s), 1 cross-module dependency path(s), 1 unknown file(s)" in result.stdout
    assert "architecture/map: unmapped files" in result.stdout


def test_root_health_passes_for_synced_recipe_workspace(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    init_result = run_cli(project_root, "workspace", "sync", "init", "--language", "python")

    result = run_cli(project_root, "health", "--top", "-1")

    assert init_result.returncode == 0, init_result.stderr
    assert result.returncode == 0, result.stderr
    assert "Enclosure Health:" in result.stdout
    assert "- Paths: target present, rules present, recipes present" in result.stdout
    assert "- Boundaries: 0 violation(s)" in result.stdout
    assert "- Shape: 0 violation(s)" in result.stdout
    assert "attention investigate architecture/clusters" in result.stdout
    assert "error blocker" not in result.stdout


def test_root_health_top_zero_keeps_blocking_counts_without_detail_sections(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "health", "--top", "0")

    assert result.returncode == 1
    assert "- Boundaries: 4 violation(s)" in result.stdout
    assert "- Shape: 11 violation(s)" in result.stdout
    assert "- Map: 2 module(s), 1 cross-module dependency path(s), 1 unknown file(s)" in result.stdout
    assert "Architecture Details:" not in result.stdout
    assert "Workspace Rule Documents:" not in result.stdout
