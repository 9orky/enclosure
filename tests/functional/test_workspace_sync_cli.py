from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_sync_init_creates_packaged_rules_and_update_preserves_them(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    init_result = run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    update_result = run_cli(project_root, "workspace", "sync", "update")
    migrate_result = run_cli(project_root, "workspace", "sync", "migrate")

    assert init_result.returncode == 0, init_result.stderr
    assert "Found .enclosure." in init_result.stdout
    assert "Created " in init_result.stdout
    assert (project_root / ".enclosure" / "rules" / "shared" / "verification" / "TESTING.md").exists()
    assert update_result.returncode == 0, update_result.stderr
    assert "Found .enclosure." in update_result.stdout
    assert "Preserved " in update_result.stdout
    assert migrate_result.returncode == 0, migrate_result.stderr
    assert "Found .enclosure." in migrate_result.stdout


def test_sync_init_without_config_reports_bad_sync_error(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "no_config_project")

    result = run_cli(project_root, "workspace", "sync", "init", "--language", "python")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Could not find a configuration file." in result.stderr
    assert ".enclosure/enclosure.yaml" in result.stderr
