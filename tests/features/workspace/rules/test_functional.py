from __future__ import annotations

from enclosure.__main__ import app
from enclosure.features.workspace.rules import application


def test_workspace_rules_accepts_valid_fixture_workspace(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    report = application.build_rule_schema_report()
    result = cli_runner.invoke(app, ["workspace", "rules"])

    assert result.exit_code == 0, result.output
    assert report.collection_complete
    assert report.documents_checked == report.documents_discovered
    assert report.documents_checked >= 3
    assert not report.has_findings
    assert "Route planning:" in result.output
    assert "Available route tags:" in result.output
    assert "structure" in result.output


def test_workspace_rules_reports_expected_broken_fixture_violations(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("broken-enclosure-workspace")
    use_project(project)

    report = application.build_rule_schema_report()
    result = cli_runner.invoke(app, ["workspace", "rules"])
    violation_codes = {
        violation.code
        for document in report.documents
        for violation in document.violations
    }

    assert result.exit_code == 1, result.output
    assert report.has_findings
    assert "local-content-too-large" in violation_codes
    assert "missing-section" in violation_codes


def test_workspace_rules_route_reports_structure_read_receipt(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(
        app,
        ["workspace", "rules", "route", "--tag", "structure"],
    )

    assert result.exit_code == 0, result.output
    assert "Read receipt" in result.output
    assert "shared/structure/INDEX.md" in result.output


def test_workspace_rules_route_infers_tags_from_path(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(
        app,
        [
            "workspace",
            "rules",
            "route",
            "--path",
            "src/enclosure/features/example/domain.py",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Selected tags: structure, python, layers" in result.output
    assert "Tag selection" in result.output


def test_workspace_rules_route_infers_tags_from_task(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(
        app,
        ["workspace", "rules", "route", "--task", "structure"],
    )

    assert result.exit_code == 0, result.output
    assert "Task category `structure` maps to `structure`" in result.output
    assert "Read receipt" in result.output


def test_workspace_rules_route_reports_unknown_tag_choices(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(
        app,
        ["workspace", "rules", "route", "--tag", "missing"],
    )

    assert result.exit_code == 1, result.output
    assert "No route matched" in result.output
    assert "structure" in result.output
