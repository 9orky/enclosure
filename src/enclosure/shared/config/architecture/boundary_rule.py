from __future__ import annotations

from ..base import StrictConfigModel


class BoundaryRule(StrictConfigModel):
    source: str
    disallow: list[str]
    allow: list[str]
    allow_same_match: bool


__all__ = ["BoundaryRule"]
