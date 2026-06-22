from __future__ import annotations

from pathlib import Path

from modwire import supported_languages
from pydantic import field_validator

from enclosure.shared import config

import enclosure.features.architecture.boundaries
import enclosure.features.architecture.clusters
import enclosure.features.architecture.health
import enclosure.features.architecture.map
import enclosure.features.architecture.pressure
import enclosure.features.architecture.shape


class ArchitectureConfig(config.StrictConfigModel):
    language: str
    root: str
    exclusions: list[str]
    boundaries: enclosure.features.architecture.boundaries.BoundariesConfig
    clusters: enclosure.features.architecture.clusters.ClustersConfig
    health: enclosure.features.architecture.health.HealthConfig
    map: enclosure.features.architecture.map.MapConfig
    pressure: enclosure.features.architecture.pressure.PressureConfig
    shape: enclosure.features.architecture.shape.ShapeConfig

    @property
    def architecture_root(self) -> str:
        return self.root

    @property
    def rules(self) -> enclosure.features.architecture.boundaries.BoundariesConfig:
        return self.boundaries

    @field_validator("language")
    @classmethod
    def known_language(cls, value: str) -> str:
        if value not in supported_languages():
            raise ValueError(f"unsupported language: {value}")
        return value

    @classmethod
    def validate_mapping(
        cls,
        raw_data: object,
        config_path: Path,
    ) -> ArchitectureConfig:
        return config.section(raw_data, "architecture", cls, config_path)


ArchitectureConfigError = config.ConfigError


__all__ = [
    "ArchitectureConfig",
    "ArchitectureConfigError",
]
