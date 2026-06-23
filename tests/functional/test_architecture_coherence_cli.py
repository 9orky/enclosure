from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_coherence_reports_stream_mapping_for_clean_fixture(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "coherence", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "Architecture Coherence:" in result.stdout
    assert "- Streams found: 1" in result.stdout
    assert "- sales/report: 3 source node(s)" in result.stdout


def test_coherence_reports_flow_finding_for_bad_import_fixture(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "violating_architecture")

    result = run_cli(project_root, "architecture", "coherence", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Streams found: 1" in result.stdout
    assert "Findings:" in result.stdout
    assert "sales/report flow:" in result.stdout


def test_coherence_reports_cross_stream_dependency_and_seam_findings(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "coherence", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Streams found: 2" in result.stdout
    assert "- Findings: 4" in result.stdout
    assert "sales/ledger dependency-pressure: cross-stream dependencies" in result.stdout
    assert "sales/report flow: _t_domain -> _t_application" in result.stdout
    assert "sales/report flow: domain -> application" not in result.stdout
    assert "sales/report seam-use: sales/report -> sales/ledger" in result.stdout


def test_coherence_top_zero_preserves_counts_without_stream_detail(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "coherence", "--top", "0")

    assert result.returncode == 0, result.stderr
    assert "- Streams found: 2" in result.stdout
    assert "- Findings: 4" in result.stdout
    assert "Streams:" not in result.stdout
    assert "sales/report flow:" not in result.stdout
    assert "sales/report seam-use:" not in result.stdout


def test_coherence_rejects_invalid_top_limit(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "architecture", "coherence", "--top", "-2")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "limit must be -1 or greater" in result.stderr


def test_coherence_reports_missing_flow_realm_tag_configuration(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    config_path = project_root / ".enclosure" / "enclosure.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "module_tag: _t_module",
            "module_tag: _t_missing",
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "coherence", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Streams found: 0" in result.stdout
    assert "- Findings: 1" in result.stdout
    assert "No configured flow realm has a matching boundary tag" in result.stdout
