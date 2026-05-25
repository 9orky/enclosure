from __future__ import annotations

from pathlib import Path

from code_map import supported_languages
from pydantic import field_validator

import enclosure.features.architecture.boundaries.domain
import enclosure.features.architecture.clusters.domain
import enclosure.features.architecture.health.domain
import enclosure.features.architecture.map.domain
import enclosure.features.architecture.shape.domain
from enclosure.shared import config


class ArchitectureConfig(config.StrictConfigModel):
    language: str
    root: str
    exclusions: list[str]
    shape: enclosure.features.architecture.shape.domain.ShapeConfig
    boundaries: enclosure.features.architecture.boundaries.domain.BoundariesConfig
    map: enclosure.features.architecture.map.domain.MapConfig
    clusters: enclosure.features.architecture.clusters.domain.ClustersConfig
    health: enclosure.features.architecture.health.domain.HealthConfig

    @property
    def architecture_root(self) -> str:
        return self.root

    @property
    def rules(self) -> enclosure.features.architecture.boundaries.domain.BoundariesConfig:
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
