from __future__ import annotations

from .. import base


class BoundaryRule(base.StrictConfigModel):
    source: str
    disallow: list[str]
    allow: list[str]
    allow_same_match: bool


__all__ = ["BoundaryRule"]
