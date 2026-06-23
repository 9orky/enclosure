from __future__ import annotations

from .. import infrastructure
from . import preview


def current_fit_service() -> preview.PatternFitService:
    return preview.PatternFitService(
        infrastructure.current_pattern_root(),
        infrastructure.load_fit_config(),
    )


__all__ = ["current_fit_service"]
