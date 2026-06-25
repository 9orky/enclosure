from __future__ import annotations

from pathlib import Path

from enclosure.features.workspace.plan import domain
from enclosure.features.workspace.plan.application import plan_application, projections
from enclosure.features.workspace.plan.application import runtime as plan_runtime_module
from enclosure.features.workspace.plan.infrastructure import EventsourcingSQLitePersistence


def _runtime(project_root: Path) -> plan_runtime_module._Runtime:
    return plan_runtime_module._Runtime(
        project_root=project_root,
        persistence=EventsourcingSQLitePersistence.for_workspace_cache(
            project_root / ".enclosure" / ".cache"
        ),
    )


def _draft_projection(content: str) -> domain.StageProjection:
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


def test_projection_writes_are_tracked_by_notification_position(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication(env=plan_runtime.persistence.environment())
    plan = app.create_plan("Projection Tracking")
    projection = _draft_projection("# Projection Tracking\n")

    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))
    notification_id = projections.project_recorded_projections(plan_runtime, app, plan)

    tracking_path = (
        tmp_path / ".enclosure" / "plans" / "projection-tracking" / ".projection-tracking"
    )

    assert (
        tmp_path / ".enclosure" / "plans" / "projection-tracking" / "DRAFT.md"
    ).read_text(encoding="utf-8") == "# Projection Tracking\n"
    assert app.projection_tracking_position() == notification_id
    assert not tracking_path.exists()


def test_projection_rewrite_is_idempotent(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication(env=plan_runtime.persistence.environment())
    plan = app.create_plan("Projection Idempotency")
    projection = _draft_projection("# Projection Idempotency\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))

    notification_id = projections.project_recorded_projections(plan_runtime, app, plan)
    repeated_notification_id = projections.project_recorded_projections(
        plan_runtime,
        app,
        plan,
    )

    draft_path = (
        tmp_path
        / ".enclosure"
        / "plans"
        / "projection-idempotency"
        / "DRAFT.md"
    )

    assert draft_path.read_text(encoding="utf-8") == "# Projection Idempotency\n"
    assert repeated_notification_id == notification_id
    assert app.projection_tracking_position() == notification_id


def test_missing_projection_file_can_be_restored_from_replayed_events(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication(env=plan_runtime.persistence.environment())
    plan = app.create_plan("Projection Restore")
    projection = _draft_projection("# Projection Restore\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))
    notification_id = projections.project_recorded_projections(plan_runtime, app, plan)
    draft_path = tmp_path / ".enclosure" / "plans" / "projection-restore" / "DRAFT.md"
    draft_path.unlink()

    replayed_plan = app.get_plan(domain.PlanId(plan.id))
    projections.project_recorded_projections(plan_runtime, app, replayed_plan, start=0)

    assert draft_path.read_text(encoding="utf-8") == "# Projection Restore\n"
    assert app.projection_tracking_position() == notification_id


def test_projection_read_model_replays_saved_events_from_notification_log(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication(env=plan_runtime.persistence.environment())
    plan = app.create_plan("Projection Replay")
    projection = _draft_projection("# Projection Replay\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)

    replay_app = plan_application.PlanApplication(
        env=plan_runtime.persistence.environment()
    )
    replayed_plan = replay_app.get_plan(domain.PlanId(plan.id))

    notification_id = projections.project_recorded_projections(
        plan_runtime,
        replay_app,
        replayed_plan,
    )

    draft_path = tmp_path / ".enclosure" / "plans" / "projection-replay" / "DRAFT.md"
    assert draft_path.read_text(encoding="utf-8") == "# Projection Replay\n"
    assert replay_app.projection_tracking_position() == notification_id


def test_stage_read_uses_materialized_projection_files(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication(env=plan_runtime.persistence.environment())
    plan = app.create_plan("Projection Fallback")
    projection = _draft_projection("# Projection Fallback\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))
    projections.project_recorded_projections(plan_runtime, app, plan)

    read_projection = projections.read_stage_projection(
        plan_runtime,
        plan,
        domain.DraftStage(),
    )

    assert read_projection.artifacts[0].content == "# Projection Fallback\n"
