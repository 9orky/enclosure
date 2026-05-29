from __future__ import annotations

from pydantic import Field, field_validator

from enclosure.shared import config


class LocalRulesConfig(config.StrictConfigModel):
    max_content_chars: int = 2400

    @field_validator("max_content_chars")
    @classmethod
    def validate_max_content_chars(cls, value: int) -> int:
        if value < -1:
            raise ValueError("Local rule content threshold must be -1 or greater")
        return value


class RulesConfig(config.StrictConfigModel):
    local: LocalRulesConfig = Field(default_factory=LocalRulesConfig)


__all__ = [
    "LocalRulesConfig",
    "RulesConfig",
]
