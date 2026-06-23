from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_boundaries_pass_for_allowed_application_to_domain_import(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 0, result.stderr
    assert "Boundaries Summary:" in result.stdout
    assert "Architecture Boundaries Passed! No violations found." in result.stdout


def test_boundaries_report_forbidden_domain_import_and_cycle(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "=== Architectural Violations Detected ===" in result.stdout
    assert (
        "- sales/report/domain -> [sales/report/application] "
        "blocked by */*/domain -> */*/application"
    ) in result.stdout
    assert (
        "- sales/report/application -> sales/report/domain -> "
        "[sales/report/application]  no-cycles"
    ) in result.stdout


def test_boundaries_report_cross_module_ui_and_domain_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "boundaries")

    assert result.returncode == 1
    assert "Edge Rule Violations:" in result.stdout
    assert (
        "- sales/report/application -> [sales/ledger/application] "
        "blocked by */* -> */*"
    ) in result.stdout
    assert (
        "- sales/report/domain -> [sales/report/application] "
        "blocked by */*/domain -> */*/application"
    ) in result.stdout
    assert (
        "- sales/report/ui -> [sales/report/infrastructure] "
        "blocked by */*/ui -> */*/infrastructure"
    ) in result.stdout
    assert "Cycle Violations:" in result.stdout
    assert (
        "- sales/report/application -> sales/report/domain -> "
        "[sales/report/application]  no-cycles"
    ) in result.stdout
