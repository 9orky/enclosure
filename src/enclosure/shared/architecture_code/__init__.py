from __future__ import annotations

from . import application

ArchitectureCodeMap = application.ArchitectureCodeMap
extract_architecture_code = application.extract_architecture_code

__all__ = [
    "ArchitectureCodeMap",
    "extract_architecture_code",
]
