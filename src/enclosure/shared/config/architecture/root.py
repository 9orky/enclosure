from __future__ import annotations

from pydantic import Field

from ..base import StrictConfigModel
from .boundaries import BoundariesConfig
from .clusters import ClustersConfig
from .health import HealthConfig
from .map import MapConfig
from .pressure import PressureConfig
from .shape import ShapeConfig


class ArchitectureConfig(StrictConfigModel):
    language: str = "python"
    root: str = "."
    exclusions: list[str] = Field(
        default_factory=lambda: [".enclosure/**", "tests/**", "libraries/**"]
    )
    boundaries: BoundariesConfig = Field(default_factory=BoundariesConfig)
    clusters: ClustersConfig = Field(default_factory=ClustersConfig)
    health: HealthConfig = Field(default_factory=HealthConfig)
    map: MapConfig = Field(default_factory=MapConfig)
    pressure: PressureConfig = Field(default_factory=PressureConfig)
    shape: ShapeConfig = Field(default_factory=ShapeConfig)

    @property
    def architecture_root(self) -> str:
        return self.root

    @property
    def rules(self) -> BoundariesConfig:
        return self.boundaries


__all__ = ["ArchitectureConfig"]
