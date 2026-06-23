from __future__ import annotations

from .errors import ScaffoldError
from .facade import ScaffoldFacade as _ScaffoldFacade
from .scaffold import RenderedScaffoldFile, Scaffold

scaffolding = _ScaffoldFacade()

__all__ = [
    "RenderedScaffoldFile",
    "Scaffold",
    "ScaffoldError",
    "scaffolding",
]
