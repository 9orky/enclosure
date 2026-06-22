from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml

from enclosure.__main__ import app
from enclosure.features.workspace.rules import application, infrastructure
from enclosure.features.workspace.rules.domain import documents, graph, metadata, policy


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


def test_packaged_shared_rule_foundation_is_valid() -> None:
    rules_root = files("enclosure").joinpath("resources", "rules")
    document_files = infrastructure.file_repository.find(rules_root)
    rule_schema_policy = policy.RuleSchemaPolicy.default()
    known_paths = {document_file.path for document_file in document_files}
    checked_documents: list[documents.RuleDocument] = []
    issues: list[str] = []

    assert len(document_files) >= 18
    assert Path("INDEX.md") in known_paths
    assert all(not document_file.is_local for document_file in document_files)

    for document_file in document_files:
        try:
            document_check = rule_schema_policy.inspect_document(document_file)
        except metadata.RuleDocumentParseError as exc:
            issues.append(f"{document_file.path.as_posix()}: {exc}")
            continue

        checked_documents.append(document_check.document)
        violations = document_check.violations + rule_schema_policy.validate_references(
            document=document_check.document,
            known_paths=known_paths,
        )
        issues.extend(
            f"{document_file.path.as_posix()}: "
            f"{violation.code}: {violation.message}"
            for violation in violations
        )

    issues.extend(
        f"{finding.path.as_posix()}: "
        f"{finding.violation.code}: {finding.violation.message}"
        for finding in graph.validate_rule_graph(tuple(checked_documents))
    )

    assert not issues, "\n".join(issues)


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
    assert "Focused checks: enclosure workspace rules" in result.output
    assert "Post-change health: enclosure health" in result.output


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
    assert "Selected tags: structure" in result.output
    assert "python" not in result.output
    assert "Tag selection" in result.output


def test_workspace_rules_route_uses_configured_architecture_tags_for_path(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    raw_config = yaml.safe_load(project.config_path.read_text(encoding="utf-8"))
    raw_config["architecture"]["boundaries"]["tags"] = [
        {"name": "module", "match": "*/*", "except": [], "exclude": []},
        {"name": "domain", "match": "*/*/domain", "except": [], "exclude": []},
    ]
    raw_config["architecture"]["boundaries"]["flow"]["layers"] = ["domain"]
    raw_config["architecture"]["boundaries"]["flow"]["module_tag"] = "module"
    project.config_path.write_text(yaml.safe_dump(raw_config), encoding="utf-8")

    result = cli_runner.invoke(
        app,
        [
            "workspace",
            "rules",
            "route",
            "--path",
            "src/example/module/domain.py",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Selected tags: structure, module, layers" in result.output
    assert "python" not in result.output


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


def test_workspace_rules_route_infers_calibration_from_task(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(
        app,
        ["workspace", "rules", "route", "--task", "calibration"],
    )

    assert result.exit_code == 0, result.output
    assert "Task category `calibration` maps to `calibration`" in result.output
    assert "shared/execution/CALIBRATION.md" in result.output


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
