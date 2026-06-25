from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from eventsourcing.domain import Aggregate, event
from eventsourcing.utils import get_topic

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


class PlanRegistry(Aggregate):
    def __init__(self, id: UUID) -> None:
        self.active_plan_id_text = ""

    def activate_plan(self, plan_id: PlanId) -> None:
        if self.active_plan_id_text:
            raise ValueError("Only one active plan may exist")
        self._activate_plan(plan_id.as_text())

    @event("PlanActivated")
    def _activate_plan(self, plan_id: str) -> None:
        self.active_plan_id_text = plan_id

    def release_plan(self, plan_id: PlanId, reason: str) -> None:
        if not self.active_plan_id_text:
            raise LookupError("No active plan exists")
        if self.active_plan_id_text != plan_id.as_text():
            raise ValueError("Active plan changed")
        self._release_plan(plan_id.as_text(), reason)

    @event("PlanReleased")
    def _release_plan(self, plan_id: str, reason: str) -> None:
        self.active_plan_id_text = ""

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
        self.questions: dict[str, questions.OpenQuestion] = {}
        self.stage_outputs: dict[str, dict[str, Any]] = {}

    def accept_stage_output(
        self,
        stage: str,
        next_stage: str,
        data_objects: list[dict[str, Any]],
        derived_slots: list[dict[str, str]],
    ) -> None:
        self._accept_stage_output(stage, next_stage, data_objects, derived_slots)

    @event("StageOutputAccepted")
    def _accept_stage_output(
        self,
        stage: str,
        next_stage: str,
        data_objects: list[dict[str, Any]],
        derived_slots: list[dict[str, str]],
    ) -> None:
        self.stage_outputs[stage] = {
            "stage": stage,
            "next_stage": next_stage,
            "data_objects": data_objects,
            "derived_slots": derived_slots,
        }

    def advance_stage(self, stage: str, state: PlanState, reason: str) -> None:
        self._advance_stage(stage, state.value, reason)

    @event("StageAdvanced")
    def _advance_stage(self, stage: str, state: str, reason: str) -> None:
        self.current_stage = stage
        self.state = PlanState(state)
        self.active = self.state != PlanState.COMPLETE

    @event("QuestionChanged")
    def _change_question(
        self,
        question_id: str,
        text: str,
        explanation: str,
        answer: str,
        status: str,
        blocking: bool,
        revisit_stage: str,
    ) -> None:
        self.questions[question_id] = questions.OpenQuestion(
            id=question_id,
            text=text,
            explanation=explanation,
            answer=answer,
            status=questions.QuestionStatus(status),
            blocking=blocking,
            revisit_stage=revisit_stage,
        )

    def ask_question(
        self,
        question_id: str,
        text: str,
        explanation: str,
        blocking: bool,
        revisit_stage: str,
    ) -> None:
        self._ask_question(
            question_id,
            text,
            explanation,
            blocking,
            revisit_stage,
        )

    @event("QuestionAsked")
    def _ask_question(
        self,
        question_id: str,
        text: str,
        explanation: str,
        blocking: bool,
        revisit_stage: str,
    ) -> None:
        self.questions[question_id] = questions.OpenQuestion(
            id=question_id,
            text=text,
            explanation=explanation,
            answer="",
            status=questions.QuestionStatus.OPEN,
            blocking=blocking,
            revisit_stage=revisit_stage,
        )

    def answer_question(
        self,
        question_id: str,
        text: str,
        explanation: str,
        answer: str,
        revisit_stage: str,
    ) -> None:
        self._answer_question(
            question_id,
            text,
            explanation,
            answer,
            revisit_stage,
        )

    @event("QuestionAnswered")
    def _answer_question(
        self,
        question_id: str,
        text: str,
        explanation: str,
        answer: str,
        revisit_stage: str,
    ) -> None:
        existing = self.questions.get(question_id)
        self.questions[question_id] = questions.OpenQuestion(
            id=question_id,
            text=existing.text if existing else text,
            explanation=existing.explanation if existing else explanation,
            answer=answer,
            status=questions.QuestionStatus.RESOLVED,
            blocking=False,
            revisit_stage=revisit_stage,
        )

    def record_projection(
        self,
        projection_id: str,
        path: str,
        stage: str,
        content: str,
    ) -> None:
        self._record_projection(projection_id, path, stage, content)

    class ProjectionRecorded(Aggregate.Event):
        class_version = 2
        projection_id: str
        path: str
        stage: str
        content: str

        @staticmethod
        def upcast_v1_v2(state: dict) -> None:
            state["content"] = ""

    @event(ProjectionRecorded)
    def _record_projection(
        self,
        projection_id: str,
        path: str,
        stage: str,
        content: str,
    ) -> None:
        return None

    def request_roll(self, reason: str, requested_stage: str) -> None:
        self._request_roll(reason, requested_stage)

    @event("RollRequested")
    def _request_roll(self, reason: str, requested_stage: str) -> None:
        return None

    def close(self, reason: str, closed_by_command: str) -> None:
        self._close(reason, closed_by_command)

    @event("Closed")
    def _close(self, reason: str, closed_by_command: str) -> None:
        self.current_stage = PlanState.COMPLETE.value
        self.state = PlanState.COMPLETE
        self.active = False


__all__ = [
    "Plan",
    "PlanId",
    "PLAN_REGISTRY_ID",
    "PlanRegistry",
    "PlanState",
    "PROJECTION_RECORDED_TOPIC",
]


PROJECTION_RECORDED_TOPIC = get_topic(Plan.ProjectionRecorded)
