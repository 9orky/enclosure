from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def validate_report_limit(value: int) -> int:
    if value < -1:
        raise ValueError("limit must be -1 or greater")
    return value


def apply_limit(items: Iterable[T], limit: int) -> tuple[T, ...]:
    if limit == -1:
        return tuple(items)
    if limit == 0:
        return ()
    return tuple(items)[:limit]


__all__ = [
    "apply_limit",
    "validate_report_limit",
]
