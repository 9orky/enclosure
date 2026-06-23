from __future__ import annotations

from collections import Counter

from pydantic import Field, model_validator

from .. import base
from . import boundary_rule, flow, tag

BOUNDARY_RULE = boundary_rule
FLOW = flow
TAG = tag


class BoundariesConfig(base.StrictConfigModel):
    tags: list[TAG.ConfigTagRule] = Field(default_factory=list)
    rules: list[BOUNDARY_RULE.BoundaryRule] = Field(default_factory=list)
    flow: FLOW.FlowRuleSet = Field(default_factory=FLOW.FlowRuleSet)

    @property
    def boundaries(self) -> list[BOUNDARY_RULE.BoundaryRule]:
        return self.rules

    @model_validator(mode="after")
    def tag_names_are_unique(self) -> BoundariesConfig:
        counts = Counter(rule.name for rule in self.tags)
        duplicates = tuple(sorted(name for name, count in counts.items() if count > 1))
        if duplicates:
            names = ", ".join(duplicates)
            raise ValueError(f"duplicate architecture boundary tag name(s): {names}")
        return self


__all__ = ["BoundariesConfig"]
