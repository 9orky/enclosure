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


def test_shape_import_flags_can_be_relaxed_without_hiding_other_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")
    config_path = project_root / ".enclosure" / "enclosure.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        .replace("allow_imports_aliases: false", "allow_imports_aliases: true")
        .replace(
            "allowed_imports_crossing_types: [module]",
            "allowed_imports_crossing_types: [module, symbol]",
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert "max_classes_per_file actual 2, limit 1" in result.stdout
    assert "allow_imports_aliases" not in result.stdout
    assert "allowed_imports_crossing_types" not in result.stdout


def test_shape_reports_aliased_imports_without_file_barrier(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    domain_path = (
        project_root
        / "src/enclosure/features/sales/report/domain.py"
    )
    domain_path.write_text(
        "\n".join(
            [
                "from pathlib import Path as FilesystemPath",
                "",
                "",
                "def total():",
                "    return FilesystemPath('x')",
            ]
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert "- sales/report/domain:pathlib allow_imports_aliases actual 1, limit 0" in result.stdout


def test_shape_reports_split_imports_without_file_barrier(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    domain_path = (
        project_root
        / "src/enclosure/features/sales/report/domain.py"
    )
    domain_path.write_text(
        "\n".join(
            [
                "from enclosure.shared.scaffolding import Scaffold",
                "from enclosure.shared.scaffolding import ScaffoldError",
                "",
                "",
                "def describe():",
                "    return (Scaffold, ScaffoldError)",
            ]
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert "- sales/report/domain:enclosure/shared enforce_joined_imports actual 2, limit 1" in result.stdout


def test_shape_reports_split_imports_without_modwire_join_key(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    domain_path = (
        project_root
        / "src/enclosure/features/sales/report/domain.py"
    )
    domain_path.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "from pathlib import PurePosixPath",
                "",
                "",
                "def total():",
                "    return (Path, PurePosixPath)",
            ]
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "shape")

    assert result.returncode == 1
    assert "- sales/report/domain:pathlib enforce_joined_imports actual 2, limit 1" in result.stdout
