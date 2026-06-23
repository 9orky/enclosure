from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_architecture_health_reports_import_and_shape_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "health", "--top", "-1")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "Architecture Health:" in result.stdout
    assert "- Boundaries: 2 violation(s)" in result.stdout
    assert "- Shape: 1 violation(s)" in result.stdout
    assert "Next: Run `enclosure architecture boundaries`" in result.stdout
    assert "Next: Run `enclosure architecture shape`" in result.stdout


def test_architecture_health_summary_reports_finding_counts(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "health", "--v")

    assert result.returncode == 1
    assert "Architecture Health (summary):" in result.stdout
    assert "- Findings:" in result.stdout


def test_architecture_health_reports_stress_fixture_aggregate_counts(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "health", "--top", "-1")

    assert result.returncode == 1
    assert "- Boundaries: 4 violation(s)" in result.stdout
    assert "- Shape: 11 violation(s)" in result.stdout
    assert "- Map: 2 module(s), 1 cross-module dependency path(s), 1 unknown file(s)" in result.stdout
    assert "- Coherence: 2 stream(s), 4 finding(s)" in result.stdout
    assert "unknown-files: unmapped" in result.stdout
