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


def test_clusters_top_zero_keeps_header_but_hides_cluster_rows(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "clusters", "--top", "0")

    assert result.returncode == 0, result.stderr
    assert "Architecture Clusters:" in result.stdout
    assert "- Group depth:" in result.stdout
    assert "Score  Files  In  Out  Internal  External  Lines  Cluster" not in result.stdout
    assert "sales/report:" not in result.stdout
    assert "- No tracked files found." in result.stdout


def test_clusters_rejects_invalid_files_top_limit(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "clusters", "--files-top", "-2")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "limit must be -1 or greater" in result.stderr


def test_clusters_respects_configured_group_depth(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")
    config_path = project_root / ".enclosure" / "enclosure.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "clusters:\n    top: -1",
            "clusters:\n    group_depth: 1\n    top: -1",
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "clusters", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Group depth: 1" in result.stdout
    assert "sales:" in result.stdout
    assert "sales/report:" not in result.stdout
    assert "sales/ledger:" not in result.stdout
