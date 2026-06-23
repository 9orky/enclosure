from __future__ import annotations

from pydantic import Field

from .. import base
from . import guidance, recipe, rules, sync

GUIDANCE = guidance
RECIPE = recipe
RULES = rules
SYNC = sync


class WorkspaceConfig(base.StrictConfigModel):
    guidance: GUIDANCE.GuidanceConfig = Field(default_factory=GUIDANCE.GuidanceConfig)
    recipe: RECIPE.RecipeConfig = Field(default_factory=RECIPE.RecipeConfig)
    rules: RULES.RulesConfig = Field(default_factory=RULES.RulesConfig)
    sync: SYNC.SyncConfig = Field(default_factory=SYNC.SyncConfig)


__all__ = ["WorkspaceConfig"]
