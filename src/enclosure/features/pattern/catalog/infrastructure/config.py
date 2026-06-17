from __future__ import annotations

import enclosure.shared.config

from ..domain import config


def load_pattern_config() -> config.PatternConfig:
    _project_root, config_path, raw_data = enclosure.shared.config.load_project_mapping()
    return enclosure.shared.config.section(
        raw_data,
        "workspace.recipe",
        config.PatternConfig,
        config_path,
    )


__all__ = ["load_pattern_config"]
