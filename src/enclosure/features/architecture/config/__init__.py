from __future__ import annotations

from . import domain, infrastructure

ArchitectureConfig = domain.ArchitectureConfig
ArchitectureConfigError = domain.ArchitectureConfigError
load_config = infrastructure.load_config

__all__ = [
    "ArchitectureConfig",
    "ArchitectureConfigError",
    "load_config",
]
