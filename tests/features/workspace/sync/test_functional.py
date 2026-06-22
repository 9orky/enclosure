from __future__ import annotations

from importlib.resources import files

import pytest
import yaml
from modwire import supported_languages as supported_source_kinds

from enclosure.__main__ import app
from enclosure.shared import layout
from tests.support.projects import FixtureProject


def _packaged_instruction(name: str) -> str:
    return files("enclosure").joinpath("resources", name).read_text(encoding="utf-8")


@pytest.mark.parametrize("source_kind", supported_source_kinds())
def test_workspace_sync_init_creates_contract_for_supported_source_fixture(
    fixture_project,
    use_project,
    cli_runner,
    source_kind: str,
) -> None:
    project = fixture_project(f"minimal-{source_kind}")
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
    assert project.copilot_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("copilot-instructions.md")
    assert project.agent_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("AGENTS.md")
    generated_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    assert generated_config["architecture"]["language"] == source_kind
    assert generated_config["architecture"]["root"] == "src"
    assert generated_config["workspace"]["recipe"]["roles_map"] == {}


def test_workspace_sync_init_requires_source_kind_for_ambiguous_source_project(
    tmp_path,
    use_project,
    cli_runner,
) -> None:
    root = tmp_path / "mixed"
    (root / "src").mkdir(parents=True)
    (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "src" / "app.ts").write_text("export const value = 1;\n", encoding="utf-8")
    project = FixtureProject(name="mixed", root=root)
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "sync", "init"])

    assert result.exit_code == 1, result.output
    assert "Ambiguous source extractor" in result.output
    assert "--language <language>" in result.output


def test_workspace_sync_init_accepts_explicit_source_kind_for_ambiguous_source_project(
    tmp_path,
    use_project,
    cli_runner,
) -> None:
    root = tmp_path / "mixed"
    (root / "src").mkdir(parents=True)
    (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "src" / "app.ts").write_text("export const value = 1;\n", encoding="utf-8")
    project = FixtureProject(name="mixed", root=root)
    use_project(project)

    result = cli_runner.invoke(
        app,
        ["workspace", "sync", "init", "--language", "typescript"],
    )

    assert result.exit_code == 0, result.output
    generated_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    assert generated_config["architecture"]["language"] == "typescript"


def test_workspace_sync_update_preserves_local_recipes_without_resource_recipe_seed(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    local_recipe_path = layout.recipe_manifest_path(project.recipes_dir / "custom-local")
    local_recipe_path.parent.mkdir(parents=True)
    local_recipe_content = "schema_version: 1\nrole: archetype\n"
    local_recipe_path.write_text(local_recipe_content, encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "update"])

    assert result.exit_code == 0, result.output
    assert local_recipe_path.read_text(encoding="utf-8") == local_recipe_content
    assert not layout.recipe_manifest_path(project.recipes_dir / "module-report-cli").exists()
    assert project.copilot_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("copilot-instructions.md")
    assert project.agent_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("AGENTS.md")


def test_workspace_sync_migrate_preserves_local_recipes_without_resource_recipe_seed(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    local_recipe_path = layout.recipe_manifest_path(project.recipes_dir / "custom-local")
    local_recipe_path.parent.mkdir(parents=True)
    local_recipe_content = "schema_version: 1\nrole: archetype\n"
    local_recipe_path.write_text(local_recipe_content, encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "migrate"])

    assert result.exit_code == 0, result.output
    assert local_recipe_path.read_text(encoding="utf-8") == local_recipe_content
    assert not layout.recipe_manifest_path(project.recipes_dir / "module-report-cli").exists()
    assert project.copilot_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("copilot-instructions.md")
    assert project.agent_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("AGENTS.md")


def test_workspace_sync_migrate_preserves_recipe_roles_map_without_unknown_warnings(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    raw_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    original_roles_map = dict(raw_config["workspace"]["recipe"]["roles_map"])

    result = cli_runner.invoke(app, ["workspace", "sync", "migrate"])

    assert result.exit_code == 0, result.output
    migrated_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    assert migrated_config["workspace"]["recipe"]["roles_map"] == original_roles_map
    assert "workspace.recipe.roles_map" not in result.output


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


def test_workspace_sync_migrate_keeps_lists_and_list_items_block_style(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    raw_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    raw_config["architecture"]["boundaries"]["tags"].append(
        {
            "name": "feature",
            "match": "src",
            "except": ["ignored"],
            "exclude": [],
        }
    )
    raw_config["workspace"]["compact_scalar_object"] = {
        "enabled": True,
        "limit": 2,
    }
    del raw_config["workspace"]["sync"]
    project.config_path.write_text(yaml.safe_dump(raw_config), encoding="utf-8")

    result = cli_runner.invoke(app, ["workspace", "sync", "migrate"])

    assert result.exit_code == 0, result.output
    migrated_text = project.config_path.read_text(encoding="utf-8")
    assert "      - except:\n" in migrated_text
    assert "        - ignored\n" in migrated_text
    assert "        exclude: []\n" in migrated_text
    assert "allowed_imports_crossing_types:\n" in migrated_text
    assert "  - module\n" in migrated_text
    assert "allowed_imports_crossing_types: [module, symbol]" not in migrated_text
    assert "compact_scalar_object: {enabled: true, limit: 2}" in migrated_text
    assert "sync: {}" in migrated_text
    assert "      - {" not in migrated_text


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
    assert project.copilot_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("copilot-instructions.md")
    assert project.agent_instructions_path.read_text(
        encoding="utf-8"
    ) == _packaged_instruction("AGENTS.md")
