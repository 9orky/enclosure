from __future__ import annotations

from . import domain

ShapeConfig = domain.ShapeConfig
ShapeConfigError = domain.ShapeConfigError
evaluate_shape = domain.evaluate_shape

__all__ = [
    "ShapeConfig",
    "ShapeConfigError",
    "evaluate_shape",
]
