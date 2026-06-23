from __future__ import annotations

from pydantic import Field
from pydantic import field_validator

from ..base import StrictConfigModel


class ClustersConfig(StrictConfigModel):
    group_depth: int = Field(default=5, ge=1, le=8)
    top: int = 20
    files_top: int = 5

    @field_validator("top", "files_top")
    @classmethod
    def value_is_limit(cls, value: int) -> int:
        if value < -1:
            raise ValueError("limit must be -1 or greater")
        return value


__all__ = ["ClustersConfig"]
