from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from eventsourcing import application, persistence
from eventsourcing.utils import get_topic

from .. import domain


SNAPSHOT_POLICY = "disabled: workspace plan streams are expected to stay small"
LEGACY_REGISTRY_MIGRATION_DEADLINE = "2026-09-30"


@dataclass(frozen=True)
class PlanStatusReport:
    project_root: Path
    database_path: Path
    current_plan_id: str
    title: str
    current_stage: str
    state: str
    active: bool
    version: int
    question_count: int
    projection_count: int
    snapshot_policy: str


@dataclass(frozen=True)
class StageAdvance:
    plan: domain.Plan
    next_projection: domain.StageProjection | None


class PlanApplication(application.Application[UUID]):
    _projection_tracking_recorder: persistence.TrackingRecorder | None = None

    def create_plan(self, title: str) -> domain.Plan:
        registry = self._get_or_create_registry()
        plan = domain.Plan(
            title=title.strip(),
            current_stage=domain.PlanState.DRAFT.value,
            source_use_case_id="manual",
            source_plan_item_id="manual",
            created_by_command="workspace plan start",
            schema_version=1,
        )
        registry.activate_plan(domain.PlanId(plan.id))
        try:
            self.save(registry, plan)
        except persistence.IntegrityError as error:
            raise ValueError("Only one active plan may exist") from error
        return self.get_plan(domain.PlanId(plan.id))

    def plan_status(
        self,
        project_root: Path,
        database_path: Path,
    ) -> PlanStatusReport:
        try:
            plan = self.get_active_plan()
        except LookupError:
            return PlanStatusReport(
                project_root=project_root,
                database_path=database_path,
                current_plan_id="",
                title="",
                current_stage="",
                state="",
                active=False,
                version=0,
                question_count=0,
                projection_count=0,
                snapshot_policy=SNAPSHOT_POLICY,
            )
        return PlanStatusReport(
            project_root=project_root,
            database_path=database_path,
            current_plan_id=str(plan.id),
            title=plan.title,
            current_stage=plan.current_stage,
            state=plan.state.value,
            active=plan.active,
            version=plan.version,
            question_count=len(plan.questions),
            projection_count=self._projection_count(plan.id),
            snapshot_policy=SNAPSHOT_POLICY,
        )

    def advance_active_plan(
        self,
        registry: domain.StageRegistry,
        projection: domain.StageProjection,
    ) -> StageAdvance:
        plan = self.get_active_plan()
        if plan.current_stage == domain.PlanState.COMPLETE.value:
            return StageAdvance(plan=plan, next_projection=None)
        stage = registry.current_for(plan)
        questions = domain.stage_questions(
            list(plan.questions.values()),
            stage.stage_id(),
        )
        blocking_questions = domain.blocking_questions(questions)
        if blocking_questions:
            raise ValueError(
                "Blocking open questions prevent stage advance: "
                + ", ".join(question.id for question in blocking_questions)
            )
        if not domain.question_cycle_passed(questions):
            raise ValueError(
                "A resolved question is required before stage advance: "
                f"{stage.stage_id()}"
            )
        review = stage.parse_review(projection)
        validation = stage.validate_review(review)
        if not validation.valid:
            raise ValueError("; ".join(validation.messages))
        result = stage.accept(review)
        plan.accept_stage_output(
            result.output.stage_id,
            result.output.next_stage_id,
            [
                {
                    "id": data_object.id,
                    "stable_identity": data_object.stable_identity,
                    "values": data_object.values,
                }
                for data_object in result.output.data_objects
            ],
            [
                {
                    "id": derived_slot.id,
                    "upstream_identity": derived_slot.upstream_identity,
                    "stage_id": derived_slot.stage_id,
                    "variant_key": derived_slot.variant_key,
                }
                for derived_slot in result.output.derived_slots
            ],
        )
        if result.output.next_stage_id == domain.PlanState.COMPLETE.value:
            plan.advance_stage(
                domain.PlanState.COMPLETE.value,
                domain.PlanState.COMPLETE,
                "Stage loop completed",
            )
            released = self.release_active_plan(plan, "Stage loop completed")
            return StageAdvance(plan=released, next_projection=None)
        next_stage = registry.next_after(stage)
        next_input = domain.StageInput(
            stage_id=next_stage.stage_id(),
            data_objects=result.output.data_objects,
        )
        plan.advance_stage(
            next_stage.stage_id(),
            domain.PlanState.ACTIVE,
            f"Accepted {stage.stage_id()} and projected {next_stage.stage_id()}",
        )
        self.save(plan)
        plan = self.get_plan(domain.PlanId(plan.id))
        return StageAdvance(
            plan=plan,
            next_projection=next_stage.scaffold(next_input),
        )

    def ask_stage_question(
        self,
        title: str,
        explanation: str,
        stage_id: str,
        artifact_path: str,
    ) -> domain.Plan:
        plan = self.get_active_plan()
        plan.ask_question(
            domain.question_id_for(stage_id, artifact_path, title),
            title,
            explanation,
            True,
            stage_id,
        )
        self.save(plan)
        return self.get_plan(domain.PlanId(plan.id))

    def answer_stage_question(
        self,
        title: str,
        answer: str,
        stage_id: str,
        artifact_path: str,
    ) -> domain.Plan:
        plan = self.get_active_plan()
        plan.answer_question(
            domain.question_id_for(stage_id, artifact_path, title),
            title,
            "This question was resolved through the workspace plan CLI.",
            answer,
            stage_id,
        )
        self.save(plan)
        return self.get_plan(domain.PlanId(plan.id))

    def request_roll(self) -> domain.Plan:
        plan = self.get_active_plan()
        plan.request_roll("workspace plan roll", plan.current_stage)
        self.save(plan)
        return self.get_plan(domain.PlanId(plan.id))

    def close_active_plan(self, reason: str) -> domain.Plan:
        plan = self.get_active_plan()
        plan.close(
            reason.strip() or "Closed by workspace plan close",
            "workspace plan close",
        )
        return self.release_active_plan(plan, "workspace plan close")

    def get_plan(self, plan_id: domain.PlanId) -> domain.Plan:
        return self.repository.get(plan_id.value)

    def get_active_plan(self) -> domain.Plan:
        return self.get_plan(self.active_plan_id())

    def active_plan_id(self) -> domain.PlanId:
        return self.get_registry().active_plan_id()

    def get_registry(self) -> domain.PlanRegistry:
        try:
            return self.repository.get(domain.PLAN_REGISTRY_ID)
        except application.AggregateNotFoundError as error:
            try:
                return self._create_registry_from_legacy_events()
            except LookupError:
                pass
            raise LookupError("No active plan exists") from error

    def release_active_plan(self, plan: domain.Plan, reason: str) -> domain.Plan:
        registry = self.get_registry()
        registry.release_plan(domain.PlanId(plan.id), reason)
        self.save(registry, plan)
        return self.get_plan(domain.PlanId(plan.id))

    def _get_or_create_registry(self) -> domain.PlanRegistry:
        try:
            return self.repository.get(domain.PLAN_REGISTRY_ID)
        except application.AggregateNotFoundError:
            try:
                return self._create_registry_from_legacy_events()
            except LookupError:
                return domain.PlanRegistry(id=domain.PLAN_REGISTRY_ID)

    def _create_registry_from_legacy_events(self) -> domain.PlanRegistry:
        registry = domain.PlanRegistry(id=domain.PLAN_REGISTRY_ID)
        registry.activate_plan(self._legacy_active_plan_id())
        try:
            self.save(registry)
        except persistence.IntegrityError:
            return self.repository.get(domain.PLAN_REGISTRY_ID)
        return self.get_registry()

    def _legacy_active_plan_id(self) -> domain.PlanId:
        active_plan_id: UUID | None = None
        for event in self._ordered_events_from_notification_log():
            if isinstance(event, domain.Plan.Created):
                active_plan_id = event.originator_id
            if isinstance(event, domain.Plan.StageAdvanced):
                if event.state == domain.PlanState.COMPLETE.value:
                    active_plan_id = None
            if isinstance(event, domain.Plan.Closed):
                active_plan_id = None
        if active_plan_id is None:
            raise LookupError("No active plan exists")
        return domain.PlanId(active_plan_id)

    def _ordered_events_from_notification_log(
        self,
        *,
        topics: tuple[str, ...] = (),
    ) -> Iterable[domain.DomainEvent]:
        start = 1
        limit = self.log_section_size
        while True:
            notifications = self.notification_log.select(
                start=start,
                limit=limit,
                topics=topics,
            )
            if not notifications:
                return
            for notification in notifications:
                yield self.mapper.to_domain_event(notification)
            start = notifications[-1].id + 1

    def _projection_count(self, plan_id: UUID) -> int:
        projection_ids: set[str] = set()
        for event in self._ordered_events_from_notification_log(
            topics=(get_topic(domain.Plan.ProjectionRecorded),)
        ):
            if (
                isinstance(event, domain.Plan.ProjectionRecorded)
                and event.originator_id == plan_id
            ):
                projection_ids.add(event.projection_id)
        return len(projection_ids)

    def projection_tracking_position(self) -> int:
        position = self.projection_tracking_recorder().max_tracking_id(self.name)
        return position or 0

    def projection_tracking_recorder(self) -> persistence.TrackingRecorder:
        if self._projection_tracking_recorder is None:
            self._projection_tracking_recorder = self.factory.tracking_recorder()
        return self._projection_tracking_recorder


__all__ = [
    "LEGACY_REGISTRY_MIGRATION_DEADLINE",
    "PlanApplication",
    "PlanStatusReport",
    "SNAPSHOT_POLICY",
    "StageAdvance",
]
