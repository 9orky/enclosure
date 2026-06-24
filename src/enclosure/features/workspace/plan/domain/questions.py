from __future__ import annotations

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
    status: QuestionStatus
    blocking: bool
    revisit_stage: str


__all__ = [
    "OpenQuestion",
    "QuestionStatus",
]
