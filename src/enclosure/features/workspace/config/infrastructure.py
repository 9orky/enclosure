from __future__ import annotations

from pathlib import Path

from enclosure.shared import config

from . import domain


def load_config() -> tuple[Path, Path, domain.WorkspaceConfig]:
    project_root, config_path, raw_data = config.load_project_mapping()
    return (
        project_root,
        config_path,
        domain.WorkspaceConfig.validate_mapping(raw_data, config_path),
    )


__all__ = [
    "load_config",
]
