from __future__ import annotations

from unittest.mock import patch

from enclosure.__main__ import app
from enclosure.features.health.report import application


def test_root_health_renders_workspace_and_architecture_sections(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["health"])

    assert result.exit_code == 0, result.output
    assert "Enclosure Health:" in result.output
    assert "Workspace:" in result.output
    assert "Architecture:" in result.output


def test_root_health_supports_three_verbosity_levels(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    summary = cli_runner.invoke(app, ["health", "--v"])
    standard = cli_runner.invoke(app, ["health", "--vv"])
    detailed = cli_runner.invoke(app, ["health", "--vvv"])

    assert summary.exit_code == 0, summary.output
    assert standard.exit_code == 0, standard.output
    assert detailed.exit_code == 0, detailed.output
    assert "Enclosure Health (summary):" in summary.output
    assert "Config:" not in summary.output
    assert "Enclosure Health:" in standard.output
    assert "Config:" in standard.output
    assert "Enclosure Health (detailed):" in detailed.output
    assert "Workspace Rule Documents:" in detailed.output
    assert "Architecture Details:" in detailed.output


def test_root_health_fails_when_workspace_health_has_blocking_findings(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("broken-enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["health"])

    assert result.exit_code == 1, result.output
    assert "workspace/rules" in result.output
    assert "workspace/recipe" in result.output
    assert "error blocker workspace/rules" in result.output
    assert "Next: Run `enclosure workspace rules`." in result.output


def test_root_health_reports_actionable_next_steps(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["health"])

    assert result.exit_code == 0, result.output
    assert "attention investigate architecture/clusters" in result.output
    assert "Next: Run `enclosure architecture clusters`." in result.output


def test_root_health_reports_lower_level_errors_as_blocking_findings(
    fixture_project,
    use_project,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    with patch(
        "enclosure.features.architecture.health.build_health_report_for_top",
        side_effect=RuntimeError("architecture exploded"),
    ):
        report = application.build_health_report_for_top(None)

    assert report.blocking_findings
    assert any(finding.detail == "architecture exploded" for finding in report.findings)
