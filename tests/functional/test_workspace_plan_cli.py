from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_plan_show_renders_plan_without_writing(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan", "sample", "--show")

    assert result.returncode == 0, result.stderr
    assert "Plan target: .enclosure/plans/sample.md" in result.stdout
    assert "# Sample" in result.stdout
    assert "## Verification Checklist" in result.stdout
    assert not (project_root / ".enclosure" / "plans" / "sample.md").exists()


def test_plan_create_preserves_existing_file_without_force(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    created = run_cli(project_root, "workspace", "plan", "sample")
    preserved = run_cli(project_root, "workspace", "plan", "sample")
    forced = run_cli(project_root, "workspace", "plan", "sample", "--force")

    assert created.returncode == 0, created.stderr
    assert (project_root / ".enclosure" / "plans" / "sample.md").is_file()
    assert preserved.returncode == 1
    assert "Preserved" in preserved.stdout
    assert forced.returncode == 0, forced.stderr
    assert "Overwrote plan .enclosure/plans/sample.md." in forced.stdout


def test_plan_requires_name(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Plan name is required" in result.stderr
