from __future__ import annotations

from unittest.mock import patch

from enclosure.__main__ import app
from enclosure.features.workspace.health import application


def test_workspace_health_accepts_valid_fixture_workspace(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "health"])

    assert result.exit_code == 0, result.output
    assert "Workspace Health:" in result.output
    assert "Workspace Health Passed" in result.output


def test_workspace_health_reports_broken_fixture_workspace(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("broken-enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "health"])

    assert result.exit_code == 1, result.output
    assert "Workspace Health:" in result.output
    assert "workspace config" not in result.output
    assert "rule documents" in result.output
    assert "recipe templates" in result.output


def test_workspace_health_reports_lower_level_errors_as_blocking_findings(
    fixture_project,
    use_project,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    with patch(
        "enclosure.features.workspace.rules.build_rule_schema_report",
        side_effect=RuntimeError("rules exploded"),
    ):
        report = application.build_workspace_health_report()

    assert report.blocking_findings
    assert any(finding.detail == "rules exploded" for finding in report.findings)
