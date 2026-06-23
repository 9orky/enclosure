from __future__ import annotations

import shutil
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


def test_architecture_health_blocks_when_no_files_are_checked(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    config_path = project_root / ".enclosure" / "enclosure.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "exclusions: [__init__.py]",
            'exclusions: ["**/*.py"]',
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "architecture", "health", "--top", "-1")

    assert result.returncode == 1
    assert "- Files checked: 0" in result.stdout
    assert "error blocker scan: code map - No files were checked." in result.stdout
    assert "Next: Fix this before review." in result.stdout


def test_architecture_health_attention_only_findings_do_not_block(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    shutil.rmtree(project_root / "src/enclosure/features/sales")
    loose_file = project_root / "src/enclosure/features/orphan.py"
    loose_file.write_text("def loose():\n    return 1\n", encoding="utf-8")

    result = run_cli(project_root, "architecture", "health", "--top", "-1")

    assert result.returncode == 0, result.stderr
    assert "- Boundaries: 0 violation(s)" in result.stdout
    assert "- Shape: 0 violation(s)" in result.stdout
    assert "- Map: 0 module(s), 0 cross-module dependency path(s), 1 unknown file(s)" in result.stdout
    assert "attention investigate map: unmapped files" in result.stdout
    assert "Architecture Health Passed! No findings." not in result.stdout


def test_architecture_health_top_zero_keeps_blocking_counts_without_detail_lists(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "stress_architecture")

    result = run_cli(project_root, "architecture", "health", "--top", "0")

    assert result.returncode == 1
    assert "- Health item limit: none" in result.stdout
    assert "- Boundaries: 4 violation(s)" in result.stdout
    assert "- Shape: 11 violation(s)" in result.stdout
    assert "Hotspots:" not in result.stdout
    assert "Pressure Clusters:" not in result.stdout
    assert "Coherence Streams:" not in result.stdout
