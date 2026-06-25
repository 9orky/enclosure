from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class QuestionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class OpenQuestion:
    id: str
    text: str
    explanation: str
    answer: str
    status: QuestionStatus
    blocking: bool
    revisit_stage: str


def blocking_questions(questions: Sequence[OpenQuestion]) -> list[OpenQuestion]:
    return [question for question in questions if question.blocking]


def answered_questions(questions: Sequence[OpenQuestion]) -> list[OpenQuestion]:
    return [
        question
        for question in questions
        if question.status == QuestionStatus.RESOLVED
    ]


def question_cycle_passed(questions: Sequence[OpenQuestion]) -> bool:
    return bool(answered_questions(questions))


def stage_questions(
    questions: Sequence[OpenQuestion],
    stage_id: str,
) -> list[OpenQuestion]:
    return [question for question in questions if question.revisit_stage == stage_id]


def question_id_for(stage_id: str, artifact_path: str, title: str) -> str:
    return ":".join(
        [
            stage_id,
            _slug(artifact_path),
            _slug(title),
        ]
    )


def _slug(value: str) -> str:
    slug = "-".join(
        "".join(character.lower() if character.isalnum() else " " for character in value)
        .split()
    )
    return slug or "question"


__all__ = [
    "answered_questions",
    "blocking_questions",
    "OpenQuestion",
    "question_cycle_passed",
    "question_id_for",
    "QuestionStatus",
    "stage_questions",
]
