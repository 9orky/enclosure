from __future__ import annotations

from pydantic import Field
from pydantic import field_validator

from ..base import StrictConfigModel


class LocalRulesConfig(StrictConfigModel):
    max_content_chars: int = 1200

    @field_validator("max_content_chars")
    @classmethod
    def validate_max_content_chars(cls, value: int) -> int:
        if value < -1:
            raise ValueError("Local rule content threshold must be -1 or greater")
        return value


class RulesConfig(StrictConfigModel):
    local: LocalRulesConfig = Field(default_factory=LocalRulesConfig)


__all__ = ["LocalRulesConfig", "RulesConfig"]
