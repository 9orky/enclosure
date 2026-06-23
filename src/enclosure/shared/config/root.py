from __future__ import annotations

from pydantic import Field

from . import base
from . import architecture, workspace

ARCHITECTURE = architecture
WORKSPACE = workspace


class EnclosureSettings(base.StrictConfigModel):
    architecture: ARCHITECTURE.ArchitectureConfig = Field(
        default_factory=ARCHITECTURE.ArchitectureConfig
    )
    workspace: WORKSPACE.WorkspaceConfig = Field(default_factory=WORKSPACE.WorkspaceConfig)


__all__ = ["EnclosureSettings"]
