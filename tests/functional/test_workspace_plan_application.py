from __future__ import annotations

from pathlib import Path

from enclosure.features.workspace.plan import domain
from enclosure.features.workspace.plan.application import plan_application


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
            "## Open Questions",
            "",
            "### Can the draft advance?",
            "",
            "The application has enough data.",
            "",
            "#### Answer",
            "",
            "Yes.",
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

    empty_status = app.plan_status(Path("."), Path("plans.sqlite"))
    created = app.create_plan("Application Status")
    active_status = app.plan_status(Path("."), Path("plans.sqlite"))

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


def test_plan_application_roll_and_close_are_event_store_commands() -> None:
    app = plan_application.PlanApplication()
    created = app.create_plan("Application Commands")

    rolled = app.request_roll()
    closed = app.close_active_plan("done")

    assert rolled.id == created.id
    assert rolled.roll_requests == ("workspace plan roll",)
    assert closed.current_stage == domain.PlanState.COMPLETE.value
    assert closed.state == domain.PlanState.COMPLETE
    assert not closed.active
    assert closed.close_reason == "done"
    assert app.plan_status(Path("."), Path("plans.sqlite")).current_plan_id == ""


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
