from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_shape_passes_when_fixture_respects_function_limit(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 0, result.stderr
    assert "Architecture Shape:" in result.stdout
    assert "Architecture Shape Passed! No violations found." in result.stdout


def test_shape_reports_function_limit_violation(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert result.stderr == ""
    assert "Shape Violations:" in result.stdout
    assert "- sales/report/domain max_functions_per_file actual 2, limit 1" in result.stdout


def test_shape_reports_multiple_file_symbol_and_import_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert "- sales/report/application:run max_declared_args_per_function actual 2, limit 1" in result.stdout
    assert "- sales/report/application:run max_lines_count_per_function actual 4, limit 3" in result.stdout
    assert "- sales/report/application:run allow_optional_function_args actual True, limit False" in result.stdout
    assert "- sales/report/domain max_classes_per_file actual 2, limit 1" in result.stdout
    assert "- sales/report/domain:Alpha max_methods_per_class actual 2, limit 1" in result.stdout
    assert "- sales/report/domain:Alpha.first max_declared_args_per_method actual 2, limit 1" in result.stdout
    assert "- sales/report/domain:Alpha.first allow_optional_method_args actual True, limit False" in result.stdout
    assert "- sales/report/application:sales/ledger/application allow_imports_aliases actual 1, limit 0" in result.stdout
    assert "- sales/report/domain:sales/report/application (symbol) allowed_imports_crossing_types actual 1, limit 0" in result.stdout
