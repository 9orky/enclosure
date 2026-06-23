from __future__ import annotations

from pydantic import Field

from .. import base


class ConfigTagRule(base.StrictConfigModel):
    name: str
    match: str
    except_: list[str] = Field(alias="except")
    exclude: list[str]

    @property
    def excluded_patterns(self) -> tuple[str, ...]:
        return (*self.except_, *self.exclude)


__all__ = ["ConfigTagRule"]
