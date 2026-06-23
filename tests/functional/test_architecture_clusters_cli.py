from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_clusters_reports_module_cluster_and_key_files(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "clusters", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "Architecture Clusters:" in result.stdout
    assert "sales/report:" in result.stdout
    assert "sales/report/application" in result.stdout
    assert "sales/report/domain" in result.stdout


def test_clusters_files_top_limits_key_file_detail(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(
        project_root,
        "architecture",
        "clusters",
        "--top",
        "-1",
        "--files-top",
        "1",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("  - sales/report/") == 1


def test_clusters_reports_multiple_clusters_and_dependency_direction(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "clusters", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "sales/report:" in result.stdout
    assert "- Depends on: sales/ledger" in result.stdout
    assert "sales/ledger:" in result.stdout
    assert "- Used by: sales/report" in result.stdout
    assert "orphan:" in result.stdout
