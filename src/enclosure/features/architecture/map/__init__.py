from __future__ import annotations

from . import domain

ArchitectureHotspot = domain.ArchitectureHotspot
MapConfig = domain.MapConfig
MappedArchitecture = domain.MappedArchitecture
describe_architecture_map = domain.describe_architecture_map

__all__ = [
    "ArchitectureHotspot",
    "MapConfig",
    "MappedArchitecture",
    "describe_architecture_map",
]
