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


def test_workspace_health_supports_three_verbosity_levels(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    summary = cli_runner.invoke(app, ["workspace", "health", "--v"])
    standard = cli_runner.invoke(app, ["workspace", "health", "--vv"])
    detailed = cli_runner.invoke(app, ["workspace", "health", "--vvv"])

    assert summary.exit_code == 0, summary.output
    assert standard.exit_code == 0, standard.output
    assert detailed.exit_code == 0, detailed.output
    assert "Workspace Health (summary):" in summary.output
    assert "Rules directory:" not in summary.output
    assert "Workspace Health:" in standard.output
    assert "Rules directory:" in standard.output
    assert "Workspace Health (detailed):" in detailed.output
    assert "Rule Documents:" in detailed.output


def test_workspace_health_rejects_multiple_verbosity_flags(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "health", "--v", "--vv"])

    assert result.exit_code == 1, result.output
    assert "Choose only one verbosity flag" in result.output


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
