from __future__ import annotations

from pathlib import Path

from eventsourcing import persistence

from enclosure.features.workspace.plan import domain
from enclosure.features.workspace.plan.application import plan_application
from enclosure.features.workspace.plan.infrastructure import (
    DEFAULT_DATABASE_NAME,
    EventsourcingSQLitePersistence,
)


def _resolved_draft_projection() -> domain.StageProjection:
    content = "\n".join(
        [
            "# Application Seam Plan",
            "",
            "## Abstract",
            "",
            "The application seam owns plan advancement.",
            "",
            "## Use Cases",
            "",
            "### Application seam",
            "",
            "Advance through the event-store boundary.",
            "",
            "#### Constraints",
            "",
            "- application owns save",
            "",
        ]
    )
    return domain.StageProjection(
        stage_id="draft",
        artifacts=[
            domain.ProjectedArtifact(
                path="DRAFT.md",
                content=content,
                artifact_kind="markdown",
            )
        ],
    )


def test_plan_application_reports_status_and_snapshot_policy() -> None:
    app = plan_application.PlanApplication()
    database_path = Path(DEFAULT_DATABASE_NAME)

    empty_status = app.plan_status(Path("."), database_path)
    created = app.create_plan("Application Status")
    active_status = app.plan_status(Path("."), database_path)

    assert empty_status.current_plan_id == ""
    assert empty_status.snapshot_policy == plan_application.SNAPSHOT_POLICY
    assert active_status.current_plan_id == str(created.id)
    assert active_status.title == "Application Status"
    assert active_status.snapshot_policy == plan_application.SNAPSHOT_POLICY


def test_plan_application_advances_stage_and_records_questions() -> None:
    app = plan_application.PlanApplication()
    app.create_plan("Application Advance")
    registry = domain.StageRegistry(
        stages=[
            domain.DraftStage(),
            domain.PlanStage(),
            domain.EpicsStage(),
        ]
    )
    app.answer_stage_question(
        "Can the draft advance?",
        "Yes.",
        "draft",
        "DRAFT.md",
    )

    advanced = app.advance_active_plan(registry, _resolved_draft_projection())

    assert advanced.plan.current_stage == "plan"
    assert advanced.next_projection is not None
    assert [artifact.path for artifact in advanced.next_projection.artifacts] == [
        "PLAN.md",
        "UML.md",
    ]
    assert len(advanced.plan.questions) == 1
    assert advanced.plan.questions["draft:draft-md:can-the-draft-advance"].status == (
        domain.QuestionStatus.RESOLVED
    )
    assert advanced.plan.questions["draft:draft-md:can-the-draft-advance"].answer == (
        "Yes."
    )


def test_plan_application_roll_and_close_are_event_store_commands() -> None:
    app = plan_application.PlanApplication()
    created = app.create_plan("Application Commands")

    rolled = app.request_roll()
    closed = app.close_active_plan("done")

    assert rolled.id == created.id
    assert closed.current_stage == domain.PlanState.COMPLETE.value
    assert closed.state == domain.PlanState.COMPLETE
    assert not closed.active
    assert app.plan_status(Path("."), Path(DEFAULT_DATABASE_NAME)).current_plan_id == ""


def test_plan_application_legacy_adapter_reads_notification_log_sections() -> None:
    app = plan_application.PlanApplication()
    app.create_plan("Notification Log")

    events = list(app._ordered_events_from_notification_log())

    assert [type(event).__name__ for event in events] == [
        "Created",
        "PlanActivated",
        "Created",
    ]
    assert plan_application.LEGACY_REGISTRY_MIGRATION_DEADLINE == "2026-09-30"


def test_plan_application_rejects_stale_concurrent_save(tmp_path: Path) -> None:
    sqlite = EventsourcingSQLitePersistence.for_workspace_cache(tmp_path)
    env = sqlite.environment()
    creator = plan_application.PlanApplication(env=env)
    creator.create_plan("Concurrent Plan")
    stale_app = plan_application.PlanApplication(env=env)
    current_app = plan_application.PlanApplication(env=env)
    stale_plan = stale_app.get_active_plan()
    current_plan = current_app.get_active_plan()

    current_plan.request_roll("current write", current_plan.current_stage)
    current_app.save(current_plan)
    stale_plan.request_roll("stale write", stale_plan.current_stage)

    try:
        stale_app.save(stale_plan)
    except persistence.IntegrityError:
        pass
    else:
        raise AssertionError("Stale concurrent save should fail by aggregate version")
