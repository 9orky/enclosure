from __future__ import annotations

from dataclasses import dataclass
from functools import singledispatchmethod
from uuid import UUID

from eventsourcing import persistence
from eventsourcing.projection import Projection
from eventsourcing.utils import get_topic

from .. import domain
from . import plan_application, runtime


PROJECTION_RECORDED_TOPIC = get_topic(domain.Plan.ProjectionRecorded)


@dataclass(frozen=True)
class PlanProjectionView:
    store: domain.ProjectionStore
    tracking_recorder: persistence.TrackingRecorder
    plan_id: UUID

    def record_tracking(self, tracking: persistence.Tracking) -> None:
        position = self.tracking_recorder.max_tracking_id(tracking.application_name)
        if position is not None and tracking.notification_id <= position:
            return
        self.tracking_recorder.insert_tracking(tracking)

    def write_recorded_projection(
        self,
        event: domain.Plan.ProjectionRecorded,
    ) -> None:
        if event.originator_id != self.plan_id or not event.content:
            return
        self.store.write_projection(
            domain.ProjectedArtifact(
                path=event.path,
                content=event.content,
                artifact_kind="markdown",
            )
        )


class PlanReadModelProjection(Projection[PlanProjectionView]):
    topics = (PROJECTION_RECORDED_TOPIC,)

    @singledispatchmethod
    def process_event(
        self,
        domain_event: domain.DomainEvent,
        tracking: persistence.Tracking,
    ) -> None:
        self.view.record_tracking(tracking)

    @process_event.register
    def _(
        self,
        domain_event: domain.Plan.ProjectionRecorded,
        tracking: persistence.Tracking,
    ) -> None:
        self.view.write_recorded_projection(domain_event)
        self.view.record_tracking(tracking)


def read_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    stage: domain.PlanningStage,
) -> domain.StageProjection:
    store = runtime.projection_store(plan_runtime, plan)
    artifacts: list[domain.ProjectedArtifact] = []
    file_models = stage.file_models(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    )
    for file_model in file_models:
        if "{" in file_model.path:
            continue
        artifacts.append(
            domain.ProjectedArtifact(
                path=file_model.path,
                content=store.read_text(file_model.path),
                artifact_kind=file_model.artifact_kind,
            )
        )
    return domain.StageProjection(stage_id=stage.stage_id(), artifacts=artifacts)


def record_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    projection: domain.StageProjection,
) -> None:
    store = runtime.projection_store(plan_runtime, plan)
    for artifact in projection.artifacts:
        projection_id = store.content_hash(artifact.content)
        plan.record_projection(
            projection_id,
            artifact.path,
            projection.stage_id,
            artifact.content,
        )


def project_recorded_projections(
    plan_runtime: runtime._Runtime,
    plan_app: plan_application.PlanApplication,
    plan: domain.Plan,
    *,
    start: int | None = None,
) -> int:
    view = PlanProjectionView(
        store=runtime.projection_store(plan_runtime, plan),
        tracking_recorder=plan_app.projection_tracking_recorder(),
        plan_id=plan.id,
    )
    projection = PlanReadModelProjection(view=view)
    start_position = (
        start
        if start is not None
        else view.tracking_recorder.max_tracking_id(plan_app.name)
    )
    next_notification_id = (start_position or 0) + 1
    while True:
        notifications = plan_app.notification_log.select(
            start=next_notification_id,
            limit=plan_app.log_section_size,
            topics=projection.topics,
        )
        if not notifications:
            return (
                view.tracking_recorder.max_tracking_id(plan_app.name)
                or start_position
                or 0
            )
        for notification in notifications:
            projection.process_event(
                plan_app.mapper.to_domain_event(notification),
                persistence.Tracking(plan_app.name, notification.id),
            )
        next_notification_id = notifications[-1].id + 1


__all__ = [
    "PlanProjectionView",
    "PlanReadModelProjection",
    "PROJECTION_RECORDED_TOPIC",
    "project_recorded_projections",
    "read_stage_projection",
    "record_stage_projection",
]
