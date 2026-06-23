from __future__ import annotations

from pydantic import Field, field_validator

from .. import base


class LocalRulesConfig(base.StrictConfigModel):
    max_content_chars: int = 1200

    @field_validator("max_content_chars")
    @classmethod
    def validate_max_content_chars(cls, value: int) -> int:
        if value < -1:
            raise ValueError("Local rule content threshold must be -1 or greater")
        return value


class RulesConfig(base.StrictConfigModel):
    local: LocalRulesConfig = Field(default_factory=LocalRulesConfig)


__all__ = ["LocalRulesConfig", "RulesConfig"]
