from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictConfigModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_default=True,
    )


__all__ = ["StrictConfigModel"]
