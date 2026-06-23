from __future__ import annotations

from pydantic import field_validator

from ..base import StrictConfigModel


class MapConfig(StrictConfigModel):
    top: int = 20

    @field_validator("top")
    @classmethod
    def top_is_limit(cls, value: int) -> int:
        if value < -1:
            raise ValueError("limit must be -1 or greater")
        return value


__all__ = ["MapConfig"]
