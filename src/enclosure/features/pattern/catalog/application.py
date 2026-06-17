from __future__ import annotations

from . import domain, infrastructure


def describe_catalog_context() -> domain.CatalogPatternContext:
    return infrastructure.load_catalog_context()


__all__ = ["describe_catalog_context"]
