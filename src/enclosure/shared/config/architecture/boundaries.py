from __future__ import annotations

from collections import Counter

from pydantic import Field
from pydantic import model_validator

from ..base import StrictConfigModel
from .boundary_rule import BoundaryRule
from .flow import FlowRuleSet
from .tag import ConfigTagRule


class BoundariesConfig(StrictConfigModel):
    tags: list[ConfigTagRule] = Field(default_factory=list)
    rules: list[BoundaryRule] = Field(default_factory=list)
    flow: FlowRuleSet = Field(default_factory=FlowRuleSet)

    @property
    def boundaries(self) -> list[BoundaryRule]:
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
