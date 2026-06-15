from __future__ import annotations

from importlib.resources import files

import pytest
import yaml
from modwire import supported_languages

from enclosure.__main__ import app


@pytest.mark.parametrize("language", supported_languages())
def test_workspace_sync_init_creates_contract_for_supported_language_fixture(
    fixture_project,
    use_project,
    cli_runner,
    language: str,
) -> None:
    project = fixture_project(f"minimal-{language}")
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "sync", "init"])

    assert result.exit_code == 0, result.output
    assert project.enclosure_dir.is_dir()
    assert project.config_path.is_file()
    assert project.plans_dir.is_dir()
    assert project.recipes_dir.is_dir()
    assert project.local_rules_dir.is_dir()
    assert project.shared_rules_dir.is_dir()
    assert project.copilot_instructions_path.is_file()
    assert project.agent_instructions_path.is_file()


def test_workspace_sync_migrate_preserves_local_recipes_without_resource_recipe_seed(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    local_recipe_path = project.recipes_dir / "custom-local" / "recipe.yaml"
    local_recipe_path.parent.mkdir(parents=True)
    local_recipe_content = "schema_version: 1\nrole: archetype\n"
    local_recipe_path.write_text(local_recipe_content, encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "migrate"])

    assert result.exit_code == 0, result.output
    assert local_recipe_path.read_text(encoding="utf-8") == local_recipe_content
    assert not (project.recipes_dir / "module-report-cli" / "recipe.yaml").exists()


def test_workspace_sync_migrate_safe_merges_config_and_warns_about_unknown_keys(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    raw_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    del raw_config["workspace"]["sync"]
    raw_config["workspace"]["unknown"] = True
    project.config_path.write_text(yaml.safe_dump(raw_config), encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "migrate"])

    assert result.exit_code == 0, result.output
    migrated_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    assert migrated_config["workspace"]["sync"] == {}
    assert migrated_config["workspace"]["unknown"] is True
    assert "CONFIG FORMAT WARNING" in result.output
    assert "Unknown config key preserved: workspace.unknown" in result.output


def test_workspace_sync_migrate_preserves_local_rules(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    local_rule_path = project.local_rules_dir / "structure" / "MODULE.md"
    local_rule_content = local_rule_path.read_text(encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "migrate"])

    assert result.exit_code == 0, result.output
    assert local_rule_path.read_text(encoding="utf-8") == local_rule_content
    assert (project.rules_dir / "shared" / "structure" / "MODULE.md").is_file()


def test_workspace_sync_update_refreshes_shared_assets_and_preserves_local_rules(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    local_rule_path = project.local_rules_dir / "structure" / "MODULE.md"
    local_rule_content = local_rule_path.read_text(encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "update"])

    assert result.exit_code == 0, result.output
    assert project.plans_dir.is_dir()
    assert local_rule_path.read_text(encoding="utf-8") == local_rule_content
    assert (
        project.shared_rules_dir / "structure" / "MODULE.md"
    ).read_text(encoding="utf-8") == files("enclosure").joinpath(
        "resources",
        "rules",
        "shared",
        "structure",
        "MODULE.md",
    ).read_text(encoding="utf-8")
    assert project.copilot_instructions_path.is_file()
    assert project.agent_instructions_path.is_file()
