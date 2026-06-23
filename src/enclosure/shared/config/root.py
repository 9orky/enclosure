from __future__ import annotations

from pydantic import Field

from .architecture import ArchitectureConfig
from .base import StrictConfigModel
from .workspace import WorkspaceConfig


class EnclosureSettings(StrictConfigModel):
    architecture: ArchitectureConfig = Field(default_factory=ArchitectureConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)


__all__ = ["EnclosureSettings"]
