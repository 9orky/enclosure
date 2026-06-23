from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_map_reports_module_layer_mapping_and_clean_dependency_counts(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "map", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "Architecture Map:" in result.stdout
    assert "- Modules found: 1" in result.stdout
    assert "- Cross-module dependencies: 0" in result.stdout
    assert "- Unknown files: 0" in result.stdout
    assert "- sales/report: 3 file(s) (application 1, domain 1)" in result.stdout


def test_map_still_reports_module_mapping_when_project_has_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "map", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Modules found: 1" in result.stdout
    assert "- sales/report: 3 file(s) (application 1, domain 1)" in result.stdout
    assert "- Unknown files: 0" in result.stdout


def test_map_reports_cross_module_dependencies_hotspots_and_unknown_files(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "map", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Modules found: 2" in result.stdout
    assert "- Cross-module dependencies: 1" in result.stdout
    assert "- Unknown files: 1" in result.stdout
    assert "- sales/ledger: 2 file(s) (application 1)" in result.stdout
    assert "- sales/report: 5 file(s) (application 1, domain 1, infrastructure 1, ui 1)" in result.stdout
    assert "- sales/report -> sales/ledger: 1" in result.stdout
    assert "- unknown-files: unmapped" in result.stdout
    assert "Unknown Files:" in result.stdout
    assert "- orphan" in result.stdout
