from __future__ import annotations

from . import domain, infrastructure

WorkspaceConfig = domain.WorkspaceConfig
WorkspaceConfigError = domain.WorkspaceConfigError
load_config = infrastructure.load_config

__all__ = [
    "WorkspaceConfig",
    "WorkspaceConfigError",
    "load_config",
]
