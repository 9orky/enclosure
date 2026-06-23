from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_pressure_reports_callable_counts_and_api_hubs(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "pressure", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "Architecture Pressure:" in result.stdout
    assert "- Callable symbols: 2" in result.stdout
    assert "- Direct calls: 1" in result.stdout
    assert "run (sales/report/application:4)" in result.stdout
    assert "total (sales/report/domain:1)" in result.stdout
    assert "Public API Hubs:" in result.stdout


def test_pressure_top_zero_keeps_counts_without_detail_sections(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "pressure", "--top", "0")

    assert result.returncode == 0, result.stderr
    assert "- Callable symbols: 2" in result.stdout
    assert "- Top limit: 0" in result.stdout
    assert "Most Calling:" not in result.stdout
    assert "Public API Hubs:" not in result.stdout


def test_pressure_reports_larger_callable_surface_and_wide_signatures(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "pressure", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Callable symbols: 9" in result.stdout
    assert "- Direct calls: 4" in result.stdout
    assert "- Unresolved internal candidates: 4" in result.stdout
    assert "run (sales/report/application:5)" in result.stdout
    assert "Alpha.first (sales/report/domain:6)" in result.stdout
    assert "Public API Hubs:" in result.stdout
    assert "sales/report/domain" in result.stdout
