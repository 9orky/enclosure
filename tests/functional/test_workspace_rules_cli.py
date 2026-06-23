from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_rules_reports_missing_rules_directory(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "rules")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Error: Workspace rules directory not found:" in result.stderr


def test_rules_report_and_route_work_after_sync_init(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    init_result = run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    report = run_cli(project_root, "workspace", "rules")
    by_task = run_cli(project_root, "workspace", "rules", "route", "--task", "verification")
    by_path = run_cli(
        project_root,
        "workspace",
        "rules",
        "route",
        "--path",
        "src/enclosure/features/sales/report/domain.py",
    )

    assert init_result.returncode == 0, init_result.stderr
    assert report.returncode == 0, report.stderr
    assert "Rule schema report." in report.stdout
    assert "Documents with issues: 0." in report.stdout
    assert by_task.returncode == 0, by_task.stderr
    assert "Selected tags: verification." in by_task.stdout
    assert "shared/verification/INDEX.md" in by_task.stdout
    assert by_path.returncode == 0, by_path.stderr
    assert "Rule read route." in by_path.stdout
    assert "Selected tags:" in by_path.stdout


def test_rules_route_requires_selection(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")

    result = run_cli(project_root, "workspace", "rules", "route")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "At least one --tag, --path, or --task is required" in result.stderr


def test_rules_reports_invalid_local_rule_document(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    bad_rule = project_root / ".enclosure" / "rules" / "local" / "custom" / "BAD.md"
    bad_rule.parent.mkdir(parents=True)
    bad_rule.write_text(
        "\n".join(
            (
                "---",
                "doc_class: policy",
                "rule_kind: policy",
                "scope: local",
                "audience: agent",
                "purpose: Broken local policy.",
                "tags: [local, broken]",
                "---",
                "",
                "# Bad",
                "",
                "## Rules",
                "",
                "- Missing checks section.",
                "",
            )
        ),
        encoding="utf-8",
    )

    result = run_cli(project_root, "workspace", "rules")

    assert result.returncode == 1
    assert "Local documents with issues: 1." in result.stdout
    assert "Documents with issues: 1." in result.stdout
    assert "local/custom/BAD.md [local]: parse-error" in result.stdout
