from __future__ import annotations

from pathlib import Path

import enclosure.features.workspace.recipe.domain
import enclosure.features.workspace.rules.domain
import enclosure.features.workspace.sync.domain
from enclosure.shared import config


class WorkspaceConfig(config.StrictConfigModel):
    recipe: enclosure.features.workspace.recipe.domain.RecipeConfig
    rules: enclosure.features.workspace.rules.domain.RulesConfig
    sync: enclosure.features.workspace.sync.domain.SyncConfig

    @classmethod
    def validate_mapping(
        cls,
        raw_data: object,
        config_path: Path,
    ) -> WorkspaceConfig:
        return config.section(raw_data, "workspace", cls, config_path)


WorkspaceConfigError = config.ConfigError


__all__ = [
    "WorkspaceConfig",
    "WorkspaceConfigError",
]
