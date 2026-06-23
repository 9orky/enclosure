from __future__ import annotations

from pydantic import Field

from ..base import StrictConfigModel
from .guidance import GuidanceConfig
from .recipe import RecipeConfig
from .rules import RulesConfig
from .sync import SyncConfig


class WorkspaceConfig(StrictConfigModel):
    guidance: GuidanceConfig = Field(default_factory=GuidanceConfig)
    recipe: RecipeConfig = Field(default_factory=RecipeConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)


__all__ = ["WorkspaceConfig"]
