from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from eventsourcing.domain import Aggregate

from . import questions


PLAN_REGISTRY_ID = UUID("00000000-0000-4000-8000-000000000001")


class PlanState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETE = "complete"


@dataclass(frozen=True)
class PlanId:
    value: UUID

    def as_text(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ProjectionRecord:
    id: str
    path: str
    stage: str


class PlanRegistry(Aggregate):
    def __init__(self, id: UUID) -> None:
        self.active_plan_id_text = ""

    class PlanActivated(Aggregate.Event):
        plan_id: str

        def apply(self, aggregate: PlanRegistry) -> None:
            aggregate.active_plan_id_text = self.plan_id

    def activate_plan(self, plan_id: PlanId) -> None:
        if self.active_plan_id_text:
            raise ValueError("Only one active plan may exist")
        self.trigger_event(
            type(self).PlanActivated,
            plan_id=plan_id.as_text(),
        )

    class PlanReleased(Aggregate.Event):
        plan_id: str
        reason: str

        def apply(self, aggregate: PlanRegistry) -> None:
            aggregate.active_plan_id_text = ""

    def release_plan(self, plan_id: PlanId, reason: str) -> None:
        if not self.active_plan_id_text:
            raise LookupError("No active plan exists")
        if self.active_plan_id_text != plan_id.as_text():
            raise ValueError("Active plan changed")
        self.trigger_event(
            type(self).PlanReleased,
            plan_id=plan_id.as_text(),
            reason=reason,
        )

    def active_plan_id(self) -> PlanId:
        if not self.active_plan_id_text:
            raise LookupError("No active plan exists")
        return PlanId(UUID(self.active_plan_id_text))


class Plan(Aggregate):
    class Created(Aggregate.Created):
        title: str
        current_stage: str
        source_use_case_id: str
        source_plan_item_id: str
        created_by_command: str
        schema_version: int

    def __init__(
        self,
        title: str,
        current_stage: str,
        source_use_case_id: str,
        source_plan_item_id: str,
        created_by_command: str,
        schema_version: int,
    ) -> None:
        self.title = title
        self.current_stage = current_stage
        self.source_use_case_id = source_use_case_id
        self.source_plan_item_id = source_plan_item_id
        self.created_by_command = created_by_command
        self.schema_version = schema_version
        self.state = PlanState.ACTIVE
        self.active = True
        self.draft_content_hash = ""
        self.questions: dict[str, questions.OpenQuestion] = {}
        self.projections: dict[str, ProjectionRecord] = {}
        self.stage_outputs: dict[str, dict[str, Any]] = {}
        self.roll_requests: tuple[str, ...] = ()
        self.close_reason = ""

    class StageOutputAccepted(Aggregate.Event):
        stage: str
        next_stage: str
        data_objects: list[dict[str, Any]]
        derived_slots: list[dict[str, str]]

        def apply(self, aggregate: Plan) -> None:
            aggregate.stage_outputs[self.stage] = {
                "stage": self.stage,
                "next_stage": self.next_stage,
                "data_objects": self.data_objects,
                "derived_slots": self.derived_slots,
            }

    def accept_stage_output(
        self,
        stage: str,
        next_stage: str,
        data_objects: list[dict[str, Any]],
        derived_slots: list[dict[str, str]],
    ) -> None:
        self.trigger_event(
            type(self).StageOutputAccepted,
            stage=stage,
            next_stage=next_stage,
            data_objects=data_objects,
            derived_slots=derived_slots,
        )

    class StageAdvanced(Aggregate.Event):
        stage: str
        state: str
        reason: str

        def apply(self, aggregate: Plan) -> None:
            aggregate.current_stage = self.stage
            aggregate.state = PlanState(self.state)
            aggregate.active = aggregate.state != PlanState.COMPLETE

    def advance_stage(self, stage: str, state: PlanState, reason: str) -> None:
        self.trigger_event(
            type(self).StageAdvanced,
            stage=stage,
            state=state.value,
            reason=reason,
        )

    class DraftUpdated(Aggregate.Event):
        content_hash: str
        source_path: str

        def apply(self, aggregate: Plan) -> None:
            aggregate.draft_content_hash = self.content_hash

    def update_draft(self, content_hash: str, source_path: str) -> None:
        self.trigger_event(
            type(self).DraftUpdated,
            content_hash=content_hash,
            source_path=source_path,
        )

    class QuestionChanged(Aggregate.Event):
        question_id: str
        text: str
        explanation: str
        status: str
        blocking: bool
        revisit_stage: str

        def apply(self, aggregate: Plan) -> None:
            aggregate.questions[self.question_id] = questions.OpenQuestion(
                id=self.question_id,
                text=self.text,
                explanation=self.explanation,
                status=questions.QuestionStatus(self.status),
                blocking=self.blocking,
                revisit_stage=self.revisit_stage,
            )

    def change_question(
        self,
        question_id: str,
        text: str,
        explanation: str,
        status: questions.QuestionStatus,
        blocking: bool,
        revisit_stage: str,
    ) -> None:
        self.trigger_event(
            type(self).QuestionChanged,
            question_id=question_id,
            text=text,
            explanation=explanation,
            status=status.value,
            blocking=blocking,
            revisit_stage=revisit_stage,
        )

    class ProjectionRecorded(Aggregate.Event):
        projection_id: str
        path: str
        stage: str

        def apply(self, aggregate: Plan) -> None:
            aggregate.projections[self.projection_id] = ProjectionRecord(
                id=self.projection_id,
                path=self.path,
                stage=self.stage,
            )

    def record_projection(
        self,
        projection_id: str,
        path: str,
        stage: str,
    ) -> None:
        self.trigger_event(
            type(self).ProjectionRecorded,
            projection_id=projection_id,
            path=path,
            stage=stage,
        )

    class RollRequested(Aggregate.Event):
        reason: str
        requested_stage: str

        def apply(self, aggregate: Plan) -> None:
            aggregate.roll_requests = (*aggregate.roll_requests, self.reason)

    def request_roll(self, reason: str, requested_stage: str) -> None:
        self.trigger_event(
            type(self).RollRequested,
            reason=reason,
            requested_stage=requested_stage,
        )

    class Closed(Aggregate.Event):
        reason: str
        closed_by_command: str

        def apply(self, aggregate: Plan) -> None:
            aggregate.close_reason = self.reason
            aggregate.current_stage = PlanState.COMPLETE.value
            aggregate.state = PlanState.COMPLETE
            aggregate.active = False

    def close(self, reason: str, closed_by_command: str) -> None:
        self.trigger_event(
            type(self).Closed,
            reason=reason,
            closed_by_command=closed_by_command,
        )


__all__ = [
    "Plan",
    "PlanId",
    "PLAN_REGISTRY_ID",
    "PlanRegistry",
    "PlanState",
    "ProjectionRecord",
]
