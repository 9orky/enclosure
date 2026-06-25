from __future__ import annotations

from pathlib import Path

from conftest import copy_fixture, run_cli


def test_plan_without_active_event_stream_reports_none(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan")

    assert result.returncode == 0, result.stderr
    assert "Plan report." in result.stdout
    assert "Event store: .enclosure/.cache/plans.sqlite" in result.stdout
    assert "Current plan: none" in result.stdout
    assert "Status: ok" in result.stdout


def test_plan_start_records_active_plan_event(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    status = run_cli(project_root, "workspace", "plan")

    assert started.returncode == 0, started.stderr
    assert "Started plan " in started.stdout
    assert "Title: Planning Workflow" in started.stdout
    assert "State: active" in started.stdout
    assert "Version: 3" in started.stdout
    assert status.returncode == 0, status.stderr
    assert "Current plan: none" not in status.stdout
    assert "Title: Planning Workflow" in status.stdout
    assert "Questions: 0" in status.stdout
    assert "Projections: 1" in status.stdout
    assert (
        project_root / ".enclosure" / "plans" / "planning-workflow" / "DRAFT.md"
    ).is_file()


def test_plan_next_projects_plan_stage_files(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    advanced = run_cli(project_root, "workspace", "plan", "next")
    status = run_cli(project_root, "workspace", "plan")

    plan_root = project_root / ".enclosure" / "plans" / "planning-workflow"

    assert started.returncode == 0, started.stderr
    assert advanced.returncode == 0, advanced.stderr
    assert "Stage: plan" in advanced.stdout
    assert (plan_root / "PLAN.md").is_file()
    assert (plan_root / "UML.md").is_file()
    assert status.returncode == 0, status.stderr
    assert "Stage: plan" in status.stdout


def test_plan_next_records_open_question_and_answer_from_stage_file(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    draft_path = (
        project_root / ".enclosure" / "plans" / "planning-workflow" / "DRAFT.md"
    )
    draft_content = draft_path.read_text(encoding="utf-8")
    draft_path.write_text(
        draft_content
        + "\n".join(
            [
                "## Open Questions",
                "",
                "### Which scope blocks the draft?",
                "",
                "We need a concrete answer before advancing.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    blocked = run_cli(project_root, "workspace", "plan", "next")
    blocked_status = run_cli(project_root, "workspace", "plan")
    draft_path.write_text(
        draft_content
        + "\n".join(
            [
                "## Open Questions",
                "",
                "### Which scope blocks the draft?",
                "",
                "We need a concrete answer before advancing.",
                "",
                "#### Answer",
                "",
                "The draft scope is complete.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    advanced = run_cli(project_root, "workspace", "plan", "next")
    advanced_status = run_cli(project_root, "workspace", "plan")

    assert started.returncode == 0, started.stderr
    assert blocked.returncode == 1
    assert "Blocking open questions prevent stage advance" in blocked.stderr
    assert "draft:draft-md:which-scope-blocks-the-draft" in blocked.stderr
    assert blocked_status.returncode == 0, blocked_status.stderr
    assert "Stage: draft" in blocked_status.stdout
    assert "Questions: 1" in blocked_status.stdout
    assert advanced.returncode == 0, advanced.stderr
    assert "Stage: plan" in advanced.stdout
    assert advanced_status.returncode == 0, advanced_status.stderr
    assert "Stage: plan" in advanced_status.stdout
    assert "Questions: 1" in advanced_status.stdout


def test_plan_agent_reports_current_stage_file_models(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    agent = run_cli(project_root, "workspace", "plan", "agent")

    assert started.returncode == 0, started.stderr
    assert agent.returncode == 0, agent.stderr
    assert "Agent context for stage: draft" in agent.stdout
    assert "- DRAFT.md [draft_seed]" in agent.stdout


def test_plan_roll_projects_epic_package_and_completes(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    rolled = run_cli(project_root, "workspace", "plan", "roll")

    epic_root = (
        project_root
        / ".enclosure"
        / "plans"
        / "planning-workflow"
        / "epics"
        / "your-use-case-name"
    )

    assert started.returncode == 0, started.stderr
    assert rolled.returncode == 0, rolled.stderr
    assert "Stage: complete" in rolled.stdout
    assert (epic_root / "EPIC.md").is_file()
    assert (epic_root / "USER_STORIES.md").is_file()
    assert (epic_root / "flows.mermaid").is_file()
    assert (epic_root / "uml.mermaid").is_file()
    assert (epic_root / "tree.mermaid").is_file()
    assert (epic_root / "SCHEMAS.md").is_file()
    schemas = (epic_root / "SCHEMAS.md").read_text(encoding="utf-8")
    assert (epic_root / "flows.mermaid").read_text(encoding="utf-8").strip() in schemas
    assert (epic_root / "uml.mermaid").read_text(encoding="utf-8").strip() in schemas
    assert (epic_root / "tree.mermaid").read_text(encoding="utf-8").strip() in schemas


def test_plan_start_rejects_second_active_plan(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    first = run_cli(project_root, "workspace", "plan", "start", "First")
    second = run_cli(project_root, "workspace", "plan", "start", "Second")
    status = run_cli(project_root, "workspace", "plan")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert "Only one active plan may exist" in second.stderr
    assert status.returncode == 0, status.stderr
    assert "Title: First" in status.stdout
    assert "Title: Second" not in status.stdout


def test_plan_close_records_terminal_event_without_deleting_files(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Closeable Plan")
    closed = run_cli(
        project_root,
        "workspace",
        "plan",
        "close",
        "Closing before projection purge.",
    )
    status = run_cli(project_root, "workspace", "plan")

    draft_path = project_root / ".enclosure" / "plans" / "closeable-plan" / "DRAFT.md"

    assert started.returncode == 0, started.stderr
    assert closed.returncode == 0, closed.stderr
    assert "Closed plan " in closed.stdout
    assert "Stage: complete" in closed.stdout
    assert "State: complete" in closed.stdout
    assert "Active: no" in closed.stdout
    assert status.returncode == 0, status.stderr
    assert "Current plan: none" in status.stdout
    assert draft_path.is_file()


def test_plan_start_requires_title_without_writing(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "plan", "start")

    assert result.returncode == 1
    assert "Plan title is required" in result.stderr
    assert not (project_root / ".enclosure" / ".cache" / "plans.sqlite").exists()


def test_root_plan_alias_reports_event_backed_status(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "plan", "start", "Alias Plan")
    result = run_cli(project_root, "plan")

    assert started.returncode == 0, started.stderr
    assert result.returncode == 0, result.stderr
    assert "Title: Alias Plan" in result.stdout
