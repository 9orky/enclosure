from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator

import enclosure.features.workspace.recipe
import enclosure.features.workspace.rules
import enclosure.features.workspace.sync
from enclosure.shared import config


class GuidanceConfig(config.StrictConfigModel):
    max_template_chars: int = 1200

    @field_validator("max_template_chars")
    @classmethod
    def validate_max_template_chars(cls, value: int) -> int:
        if value < -1:
            raise ValueError("Guidance template threshold must be -1 or greater")
        return value


class WorkspaceConfig(config.StrictConfigModel):
    guidance: GuidanceConfig = Field(default_factory=GuidanceConfig)
    recipe: enclosure.features.workspace.recipe.RecipeConfig
    rules: enclosure.features.workspace.rules.RulesConfig
    sync: enclosure.features.workspace.sync.SyncConfig

    @classmethod
    def validate_mapping(
        cls,
        raw_data: object,
        config_path: Path,
    ) -> WorkspaceConfig:
        return config.section(raw_data, "workspace", cls, config_path)


WorkspaceConfigError = config.ConfigError


__all__ = [
    "GuidanceConfig",
    "WorkspaceConfig",
    "WorkspaceConfigError",
]
