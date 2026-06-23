from __future__ import annotations

from pathlib import Path
from textwrap import dedent

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


def test_sync_update_repairs_shared_rules_and_preserves_local_rules(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    shared_rule = (
        project_root / ".enclosure" / "rules" / "shared" / "verification" / "TESTING.md"
    )
    shared_rule.write_text("broken shared rule\n", encoding="utf-8")
    local_rule = project_root / ".enclosure" / "rules" / "local" / "custom" / "LOCAL.md"
    _write_file(
        local_rule,
        """
        ---
        doc_class: policy
        rule_kind: policy
        scope: local
        audience: agent
        purpose: Preserve local policy.
        applies_when:
          - Testing sync update local preservation.
        tags:
          - local
          - custom
        read_directly: false
        tightens_paths:
          - ../../shared/verification/TESTING.md
        ---

        # Local

        ## Rules

        - Keep this local file.

        ## Checks

        - The file still exists after sync update.
        """,
    )

    update_result = run_cli(project_root, "workspace", "sync", "update")
    rules_result = run_cli(project_root, "workspace", "rules")

    assert update_result.returncode == 0, update_result.stderr
    assert "Updated " in update_result.stdout
    assert shared_rule.read_text(encoding="utf-8") != "broken shared rule\n"
    assert local_rule.is_file()
    assert "Keep this local file." in local_rule.read_text(encoding="utf-8")
    assert rules_result.returncode == 0, rules_result.stderr
    assert "Documents with issues: 0." in rules_result.stdout


def test_sync_migrate_preserves_project_owned_recipe_roles_map(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    result = run_cli(project_root, "workspace", "sync", "migrate")
    config_text = (project_root / ".enclosure" / "enclosure.yaml").read_text(
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert "Found .enclosure." in result.stdout
    assert "orders/report: compact" in config_text
    assert "pressure:" in config_text


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
