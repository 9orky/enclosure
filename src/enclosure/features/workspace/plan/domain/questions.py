from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class QuestionArtifact(Protocol):
    path: str
    content: str


class QuestionProjection(Protocol):
    stage_id: str
    artifacts: Sequence[QuestionArtifact]


class QuestionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class OpenQuestion:
    id: str
    text: str
    explanation: str
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
    if not questions:
        return True
    return bool(answered_questions(questions))


def extract_open_questions(projection: QuestionProjection) -> list[OpenQuestion]:
    questions: list[OpenQuestion] = []
    for artifact in projection.artifacts:
        questions.extend(
            _extract_artifact_questions(
                projection.stage_id,
                artifact.path,
                artifact.content,
            )
        )
    return questions


def append_open_question(content: str, question: str, explanation: str) -> str:
    question_block = "\n".join(
        [
            "",
            f"### {question.strip()}",
            "",
            explanation.strip(),
            "",
        ]
    )
    if "## Open Questions" in content:
        return content.rstrip() + "\n" + question_block
    return content.rstrip() + "\n\n## Open Questions\n" + question_block


def append_question_answer(
    stage_id: str,
    artifact_path: str,
    content: str,
    question_id: str,
    answer: str,
) -> str:
    lines = content.splitlines()
    output: list[str] = []
    in_open_questions = False
    in_target_question = False
    inserted = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_target_question and not inserted:
                output.extend(_answer_lines(answer))
                inserted = True
            in_open_questions = stripped[3:].strip().lower() == "open questions"
            in_target_question = False
            output.append(line)
            continue
        if in_open_questions and stripped.startswith("### "):
            if in_target_question and not inserted:
                output.extend(_answer_lines(answer))
                inserted = True
            title = stripped[4:].strip()
            in_target_question = (
                ":".join([stage_id, _slug(artifact_path), _slug(title)])
                == question_id
            )
            output.append(line)
            continue
        output.append(line)
    if in_target_question and not inserted:
        output.extend(_answer_lines(answer))
        inserted = True
    if not inserted:
        raise ValueError(f"Question not found in current stage files: {question_id}")
    return "\n".join(output).rstrip() + "\n"


def _extract_artifact_questions(
    stage_id: str,
    artifact_path: str,
    content: str,
) -> list[OpenQuestion]:
    extracted: list[OpenQuestion] = []
    in_questions = False
    active_title = ""
    explanation_lines: list[str] = []
    answer_lines: list[str] = []
    active_detail = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if active_title:
                extracted.append(
                    _question_from_parts(
                        stage_id,
                        artifact_path,
                        active_title,
                        explanation_lines,
                        answer_lines,
                    )
                )
            in_questions = stripped[3:].strip().lower() == "open questions"
            active_title = ""
            explanation_lines = []
            answer_lines = []
            active_detail = ""
            continue
        if not in_questions:
            continue
        if stripped.startswith("### "):
            if active_title:
                extracted.append(
                    _question_from_parts(
                        stage_id,
                        artifact_path,
                        active_title,
                        explanation_lines,
                        answer_lines,
                    )
                )
            active_title = stripped[4:].strip()
            explanation_lines = []
            answer_lines = []
            active_detail = "explanation"
            continue
        if not active_title:
            continue
        if stripped.startswith("#### "):
            active_detail = stripped[5:].strip().lower()
            continue
        if not stripped or stripped.startswith("[comment]:"):
            continue
        if active_detail == "answer":
            answer_lines.append(stripped)
            continue
        explanation_lines.append(stripped)
    if active_title:
        extracted.append(
            _question_from_parts(
                stage_id,
                artifact_path,
                active_title,
                explanation_lines,
                answer_lines,
            )
        )
    return extracted


def _question_from_parts(
    stage_id: str,
    artifact_path: str,
    title: str,
    explanation_lines: list[str],
    answer_lines: list[str],
) -> OpenQuestion:
    question_id = ":".join(
        [
            stage_id,
            _slug(artifact_path),
            _slug(title),
        ]
    )
    answer = " ".join(answer_lines).strip()
    explanation = " ".join(explanation_lines).strip()
    if answer:
        status = QuestionStatus.RESOLVED
        blocking = False
        explanation = explanation or answer
    else:
        status = QuestionStatus.OPEN
        blocking = True
    return OpenQuestion(
        id=question_id,
        text=title,
        explanation=explanation,
        status=status,
        blocking=blocking,
        revisit_stage=stage_id,
    )


def _slug(value: str) -> str:
    slug = "-".join(
        "".join(character.lower() if character.isalnum() else " " for character in value)
        .split()
    )
    return slug or "question"


def _answer_lines(answer: str) -> list[str]:
    return ["", "#### Answer", "", answer.strip(), ""]


__all__ = [
    "append_open_question",
    "append_question_answer",
    "answered_questions",
    "blocking_questions",
    "extract_open_questions",
    "OpenQuestion",
    "question_cycle_passed",
    "QuestionStatus",
]
