from __future__ import annotations

from pathlib import Path
from textwrap import dedent

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


def test_rules_route_reports_unknown_tag_without_crashing(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")

    result = run_cli(project_root, "workspace", "rules", "route", "--tag", "not-a-tag")

    assert result.returncode == 1
    assert "Rule read route." in result.stdout
    assert "Selected tags: not-a-tag." in result.stdout
    assert "No route matched the requested tag set." in result.stdout
    assert result.stderr == ""


def test_rules_route_fails_on_unparseable_rule_documents(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    _write_file(
        project_root / ".enclosure" / "rules" / "local" / "custom" / "BROKEN.md",
        "# Missing frontmatter\n",
    )

    result = run_cli(
        project_root,
        "workspace",
        "rules",
        "route",
        "--task",
        "verification",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Rule route planning requires parseable rule documents" in result.stderr
    assert "local/custom/BROKEN.md" in result.stderr


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


def test_rules_reports_local_rule_without_shared_anchor(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    local_rule = project_root / ".enclosure" / "rules" / "local" / "custom" / "FLOATING.md"
    _write_file(
        local_rule,
        """
        ---
        doc_class: policy
        rule_kind: policy
        scope: local
        audience: agent
        purpose: Floating local policy.
        applies_when:
          - Testing local anchor validation.
        tags:
          - local
          - floating
        read_directly: false
        ---

        # Floating

        ## Rules

        - This local policy has no shared anchor.

        ## Checks

        - The schema report rejects the document.
        """,
    )

    result = run_cli(project_root, "workspace", "rules")

    assert result.returncode == 1
    assert "Local documents with issues: 1." in result.stdout
    assert "local/custom/FLOATING.md [local]:" in result.stdout
    assert "local-rule-without-shared-anchor" in result.stdout
    assert "unreachable-rule-document" in result.stdout


def test_rules_route_infers_tags_from_recipe_config_test_and_absolute_paths(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    run_cli(project_root, "workspace", "sync", "init", "--language", "python")
    source_path = project_root / "src/enclosure/features/sales/report/domain.py"

    result = run_cli(
        project_root,
        "workspace",
        "rules",
        "route",
        "--path",
        ".enclosure/recipes/module/recipe.yaml",
        "--path",
        ".enclosure/enclosure.yaml",
        "--path",
        "tests/functional/test_workspace_rules_cli.py",
        "--path",
        str(source_path),
    )

    assert result.returncode == 0, result.stderr
    assert "Rule read route." in result.stdout
    assert "Selected tags:" in result.stdout
    for tag in ("execution", "architecture", "verification", "structure", "module", "layers"):
        assert tag in result.stdout
    assert "`.enclosure/recipes/module/recipe.yaml` is a workspace recipe path." in result.stdout
    assert "`.enclosure/enclosure.yaml` is the architecture contract." in result.stdout
    assert "`tests/functional/test_workspace_rules_cli.py` is a test path." in result.stdout
    assert "matches a configured architecture layer tag" in result.stdout


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
