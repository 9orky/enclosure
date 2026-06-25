from __future__ import annotations

from pathlib import Path

from enclosure.features.workspace.plan import domain
from enclosure.features.workspace.plan.application import plan_application, projections
from enclosure.features.workspace.plan.application import runtime as plan_runtime_module


def _runtime(project_root: Path) -> plan_runtime_module._Runtime:
    return plan_runtime_module._Runtime(
        project_root=project_root,
        database_path=project_root / ".enclosure" / ".cache" / "plans.sqlite",
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
    app = plan_application.PlanApplication()
    plan = app.create_plan("Projection Tracking")
    projection = _draft_projection("# Projection Tracking\n")

    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))
    notification_id = app.notification_log_position()
    projections.write_stage_projection(
        plan_runtime,
        plan,
        projection,
        notification_id,
    )

    store = plan_runtime_module.projection_store(plan_runtime, plan)

    assert store.tracking_position() == notification_id


def test_projection_rewrite_is_idempotent(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication()
    plan = app.create_plan("Projection Idempotency")
    projection = _draft_projection("# Projection Idempotency\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))
    notification_id = app.notification_log_position()

    projections.write_stage_projection(plan_runtime, plan, projection, notification_id)
    projections.write_stage_projection(plan_runtime, plan, projection, notification_id)

    draft_path = (
        tmp_path
        / ".enclosure"
        / "plans"
        / "projection-idempotency"
        / "DRAFT.md"
    )
    store = plan_runtime_module.projection_store(plan_runtime, plan)

    assert draft_path.read_text(encoding="utf-8") == "# Projection Idempotency\n"
    assert store.tracking_position() == notification_id


def test_missing_projection_file_can_be_restored_from_replayed_events(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication()
    plan = app.create_plan("Projection Restore")
    projection = _draft_projection("# Projection Restore\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))
    notification_id = app.notification_log_position()
    projections.write_stage_projection(plan_runtime, plan, projection, notification_id)
    draft_path = tmp_path / ".enclosure" / "plans" / "projection-restore" / "DRAFT.md"
    draft_path.unlink()

    replayed_plan = app.get_plan(domain.PlanId(plan.id))
    projections.restore_recorded_projections(
        plan_runtime,
        replayed_plan,
        notification_id,
    )

    assert draft_path.read_text(encoding="utf-8") == "# Projection Restore\n"


def test_stage_read_falls_back_to_recorded_projection_content(
    tmp_path: Path,
) -> None:
    plan_runtime = _runtime(tmp_path)
    app = plan_application.PlanApplication()
    plan = app.create_plan("Projection Fallback")
    projection = _draft_projection("# Projection Fallback\n")
    projections.record_stage_projection(plan_runtime, plan, projection)
    app.save(plan)
    plan = app.get_plan(domain.PlanId(plan.id))

    read_projection = projections.read_stage_projection(
        plan_runtime,
        plan,
        domain.DraftStage(),
    )

    assert read_projection.artifacts[0].content == "# Projection Fallback\n"
