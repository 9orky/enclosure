from __future__ import annotations

from pydantic import Field

from .. import base
from . import boundaries, clusters, health, map, pressure, shape

BOUNDARIES = boundaries
CLUSTERS = clusters
HEALTH = health
MAP = map
PRESSURE = pressure
SHAPE = shape


class ArchitectureConfig(base.StrictConfigModel):
    language: str = ""
    root: str = "."
    exclusions: list[str] = Field(default_factory=list)
    boundaries: BOUNDARIES.BoundariesConfig = Field(
        default_factory=BOUNDARIES.BoundariesConfig
    )
    clusters: CLUSTERS.ClustersConfig = Field(default_factory=CLUSTERS.ClustersConfig)
    health: HEALTH.HealthConfig = Field(default_factory=HEALTH.HealthConfig)
    map: MAP.MapConfig = Field(default_factory=MAP.MapConfig)
    pressure: PRESSURE.PressureConfig = Field(default_factory=PRESSURE.PressureConfig)
    shape: SHAPE.ShapeConfig = Field(default_factory=SHAPE.ShapeConfig)

    @property
    def architecture_root(self) -> str:
        return self.root

    @property
    def rules(self) -> BOUNDARIES.BoundariesConfig:
        return self.boundaries


__all__ = ["ArchitectureConfig"]
