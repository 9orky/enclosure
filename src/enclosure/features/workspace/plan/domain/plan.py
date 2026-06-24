from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from eventsourcing.domain import Aggregate

from . import questions


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

    class StageOutputAccepted(Aggregate.Event):
        stage: str
        next_stage: str
        data_objects: tuple[dict[str, Any], ...]
        derived_slots: tuple[dict[str, str], ...]

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
        data_objects: tuple[dict[str, Any], ...],
        derived_slots: tuple[dict[str, str], ...],
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


__all__ = [
    "Plan",
    "PlanId",
    "PlanState",
    "ProjectionRecord",
]
