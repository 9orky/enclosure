from __future__ import annotations

from importlib.resources import files

import pytest
from code_map import supported_languages

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
    assert project.recipes_dir.is_dir()
    assert project.local_rules_dir.is_dir()
    assert project.shared_rules_dir.is_dir()
    assert project.copilot_instructions_path.is_file()
    assert project.agent_instructions_path.is_file()
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
