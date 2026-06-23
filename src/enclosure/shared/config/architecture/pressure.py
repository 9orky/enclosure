from __future__ import annotations

from pydantic import field_validator

from .. import base


class PressureConfig(base.StrictConfigModel):
    top: int = 10

    @field_validator("top")
    @classmethod
    def top_is_limit(cls, value: int) -> int:
        if value < -1:
            raise ValueError("limit must be -1 or greater")
        return value


__all__ = ["PressureConfig"]
