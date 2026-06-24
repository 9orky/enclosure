from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from eventsourcing.domain import DomainEvent

from . import plan, questions


class PlanChange(Protocol):
    def apply(self, target: plan.Plan) -> None:
        ...


@dataclass(frozen=True)
class StageChange:
    stage: str
    state: plan.PlanState
    reason: str

    def apply(self, target: plan.Plan) -> None:
        target.change_stage(self.stage, self.state, self.reason)


@dataclass(frozen=True)
class DraftChange:
    content_hash: str
    source_path: str

    def apply(self, target: plan.Plan) -> None:
        target.update_draft(self.content_hash, self.source_path)


@dataclass(frozen=True)
class QuestionChange:
    question_id: str
    text: str
    explanation: str
    status: questions.QuestionStatus
    blocking: bool
    revisit_stage: str

    def apply(self, target: plan.Plan) -> None:
        target.change_question(
            self.question_id,
            self.text,
            self.explanation,
            self.status,
            self.blocking,
            self.revisit_stage,
        )


@dataclass(frozen=True)
class ProjectionChange:
    projection_id: str
    path: str
    stage: str

    def apply(self, target: plan.Plan) -> None:
        target.register_projection(self.projection_id, self.path, self.stage)


@dataclass(frozen=True)
class RollRequest:
    reason: str
    requested_stage: str

    def apply(self, target: plan.Plan) -> None:
        target.request_roll(self.reason, self.requested_stage)


__all__ = [
    "DomainEvent",
    "DraftChange",
    "PlanChange",
    "ProjectionChange",
    "QuestionChange",
    "RollRequest",
    "StageChange",
]
