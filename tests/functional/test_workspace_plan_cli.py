from __future__ import annotations

from pathlib import Path
import shutil

from conftest import copy_fixture, run_cli


def _append_resolved_question(path: Path, title: str, answer: str) -> None:
    content = path.read_text(encoding="utf-8")
    path.write_text(
        content.rstrip()
        + "\n\n"
        + "\n".join(
            [
                "## Open Questions",
                "",
                f"### {title}",
                "",
                "This must be answered before the stage can advance.",
                "",
                "#### Answer",
                "",
                answer,
                "",
            ]
        ),
        encoding="utf-8",
    )


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
    blocked = run_cli(project_root, "workspace", "plan", "next")
    _append_resolved_question(
        project_root / ".enclosure" / "plans" / "planning-workflow" / "DRAFT.md",
        "Is the draft ready for planning?",
        "The draft is ready for planning.",
    )
    advanced = run_cli(project_root, "workspace", "plan", "next")
    status = run_cli(project_root, "workspace", "plan")

    plan_root = project_root / ".enclosure" / "plans" / "planning-workflow"

    assert started.returncode == 0, started.stderr
    assert blocked.returncode == 1
    assert "A resolved question is required before stage advance: draft" in blocked.stderr
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


def test_plan_put_and_answer_advance_draft_without_file_edits(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    draft_content = "\n".join(
        [
            "# CLI Authored Plan",
            "",
            "## Abstract",
            "",
            "The deterministic CLI path writes stage content through workspace plan.",
            "",
            "## Use Cases",
            "",
            "### CLI authored stage",
            "",
            "The agent produces the stage text through the plan command.",
            "",
            "#### Constraints",
            "",
            "- no direct projection file edit",
            "- stage data moves through next",
            "",
        ]
    )

    started = run_cli(project_root, "workspace", "plan", "start", "CLI Authored Plan")
    put = run_cli(project_root, "workspace", "plan", "put", "DRAFT.md", draft_content)
    answered = run_cli(
        project_root,
        "workspace",
        "plan",
        "answer",
        "Can the CLI-authored draft advance?",
        "Yes. The draft was authored through the CLI.",
    )
    advanced = run_cli(project_root, "workspace", "plan", "next")

    assert started.returncode == 0, started.stderr
    assert put.returncode == 0, put.stderr
    assert "Updated artifact DRAFT.md." in put.stdout
    assert answered.returncode == 0, answered.stderr
    assert "Answered question: Can the CLI-authored draft advance?" in answered.stdout
    assert advanced.returncode == 0, advanced.stderr
    assert "Stage: plan" in advanced.stdout
    plan_content = (
        project_root / ".enclosure" / "plans" / "cli-authored-plan" / "PLAN.md"
    ).read_text(encoding="utf-8")
    assert "cli-authored-stage" in plan_content
    assert "no direct projection file edit" in plan_content


def test_plan_put_rejects_paths_outside_current_stage(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Path Guard")
    escaped = run_cli(
        project_root,
        "workspace",
        "plan",
        "put",
        "../DRAFT.md",
        "# Escaped",
    )
    undeclared = run_cli(
        project_root,
        "workspace",
        "plan",
        "put",
        "NOT_DRAFT.md",
        "# Undeclared",
    )

    assert started.returncode == 0, started.stderr
    assert escaped.returncode == 1
    assert "Artifact path must stay inside the active plan" in escaped.stderr
    assert undeclared.returncode == 1
    assert "Artifact path is not declared by the current stage" in undeclared.stderr


def test_plan_next_projects_epic_package_and_completes(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    epic_root = (
        project_root
        / ".enclosure"
        / "plans"
        / "planning-workflow"
        / "epics"
        / "your-use-case-name"
    )
    plan_root = project_root / ".enclosure" / "plans" / "planning-workflow"

    _append_resolved_question(
        plan_root / "DRAFT.md",
        "Can the draft become a plan?",
        "The draft can become a plan.",
    )
    planned = run_cli(project_root, "workspace", "plan", "next")
    _append_resolved_question(
        plan_root / "PLAN.md",
        "Can the plan become epics?",
        "The plan can become epics.",
    )
    epics = run_cli(project_root, "workspace", "plan", "next")
    _append_resolved_question(
        epic_root / "EPIC.md",
        "Can the epic package complete?",
        "The epic package can complete.",
    )
    completed = run_cli(project_root, "workspace", "plan", "next")

    assert started.returncode == 0, started.stderr
    assert planned.returncode == 0, planned.stderr
    assert "Stage: plan" in planned.stdout
    assert epics.returncode == 0, epics.stderr
    assert "Stage: epics" in epics.stdout
    assert completed.returncode == 0, completed.stderr
    assert "Stage: complete" in completed.stdout
    assert (epic_root / "EPIC.md").is_file()
    assert (epic_root / "USER_STORIES.md").is_file()
    assert (epic_root / "flows.mermaid").is_file()
    assert (epic_root / "uml.mermaid").is_file()
    assert (epic_root / "tree.mermaid").is_file()
    assert (epic_root / "SCHEMAS.md").is_file()
    event_modeling = plan_root / "eventmodeling.mermaid"
    assert event_modeling.is_file()
    event_modeling_content = event_modeling.read_text(encoding="utf-8")
    assert event_modeling_content.startswith("eventmodeling\n")
    assert "tf 10 ui Plan.YourUseCaseName" in event_modeling_content
    assert (
        "tf 16 evt WorkspacePlan.YourUseCaseNameEpicProjected ->> 15"
        in event_modeling_content
    )
    schemas = (epic_root / "SCHEMAS.md").read_text(encoding="utf-8")
    assert (epic_root / "flows.mermaid").read_text(encoding="utf-8").strip() in schemas
    assert (epic_root / "uml.mermaid").read_text(encoding="utf-8").strip() in schemas
    assert (epic_root / "tree.mermaid").read_text(encoding="utf-8").strip() in schemas


def test_plan_roll_requires_resolved_stage_question(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    started = run_cli(project_root, "workspace", "plan", "start", "Planning Workflow")
    rolled = run_cli(project_root, "workspace", "plan", "roll")

    assert started.returncode == 0, started.stderr
    assert rolled.returncode == 1
    assert "A resolved question is required before stage advance: draft" in rolled.stderr


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


def test_plan_restore_regenerates_active_projection_files_from_event_store(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")
    draft_content = "\n".join(
        [
            "# Restorable Plan",
            "",
            "## Abstract",
            "",
            "The event stream can regenerate projection files.",
            "",
            "## Use Cases",
            "",
            "### Restore projection files",
            "",
            "Regenerate the active plan folder after projection purge.",
            "",
            "#### Constraints",
            "",
            "- source remains the event store",
            "",
        ]
    )

    started = run_cli(project_root, "workspace", "plan", "start", "Restorable Plan")
    put = run_cli(project_root, "workspace", "plan", "put", "DRAFT.md", draft_content)
    answered = run_cli(
        project_root,
        "workspace",
        "plan",
        "answer",
        "Can projections be restored?",
        "Yes. The event store has the recorded projection content.",
    )
    planned = run_cli(project_root, "workspace", "plan", "next")
    plan_root = project_root / ".enclosure" / "plans" / "restorable-plan"
    shutil.rmtree(plan_root)
    restored = run_cli(project_root, "workspace", "plan", "restore")

    assert started.returncode == 0, started.stderr
    assert put.returncode == 0, put.stderr
    assert answered.returncode == 0, answered.stderr
    assert planned.returncode == 0, planned.stderr
    assert restored.returncode == 0, restored.stderr
    assert "Restored projections for plan " in restored.stdout
    assert (plan_root / "DRAFT.md").read_text(encoding="utf-8") == (
        draft_content.rstrip()
        + "\n\n## Open Questions\n\n"
        + "### Can projections be restored?\n\n"
        + "This question was resolved through the workspace plan CLI.\n\n"
        + "#### Answer\n\n"
        + "Yes. The event store has the recorded projection content.\n"
    )
    assert (plan_root / "PLAN.md").is_file()
    assert (plan_root / "UML.md").is_file()


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
