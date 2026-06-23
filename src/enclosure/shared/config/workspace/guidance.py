from __future__ import annotations

from pydantic import field_validator

from ..base import StrictConfigModel


class GuidanceConfig(StrictConfigModel):
    max_template_chars: int = 1200

    @field_validator("max_template_chars")
    @classmethod
    def validate_max_template_chars(cls, value: int) -> int:
        if value < -1:
            raise ValueError("Guidance template threshold must be -1 or greater")
        return value


__all__ = ["GuidanceConfig"]
