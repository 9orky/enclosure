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


def test_plan_rejects_path_traversal_names_without_writing(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan", "../escape")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Plan name must be a kebab-case slug without path separators" in result.stderr
    assert not (project_root / ".enclosure" / "escape.md").exists()
    assert not (project_root / "escape.md").exists()


def test_plan_rejects_path_like_names_without_writing(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan", "bad/name")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Plan name must be a kebab-case slug without path separators" in result.stderr
    assert not (project_root / ".enclosure" / "plans" / "bad").exists()


def test_plan_rejects_non_kebab_case_names(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan", "NotKebab")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Plan name must be a kebab-case slug without path separators" in result.stderr


def test_plan_show_force_still_does_not_overwrite_existing_plan(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    plan_path = project_root / ".enclosure" / "plans" / "sample.md"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("sentinel\n", encoding="utf-8")

    result = run_cli(project_root, "workspace", "plan", "sample", "--show", "--force")

    assert result.returncode == 0, result.stderr
    assert "Plan target: .enclosure/plans/sample.md" in result.stdout
    assert "# Sample" in result.stdout
    assert plan_path.read_text(encoding="utf-8") == "sentinel\n"
