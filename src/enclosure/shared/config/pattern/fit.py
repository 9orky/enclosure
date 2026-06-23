from __future__ import annotations

from pydantic import field_validator

from ..base import StrictConfigModel


class PatternFitConfig(StrictConfigModel):
    skip: tuple[str, ...]

    @field_validator("skip")
    @classmethod
    def normalize_skip_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            value.strip().replace("\\", "/")
            for value in values
            if value.strip()
        )


__all__ = ["PatternFitConfig"]
