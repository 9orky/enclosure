from __future__ import annotations

from enclosure.shared import layout

from . import domain


def load_catalog_context() -> domain.CatalogPatternContext:
    project_root = layout.current_project_root()
    return domain.CatalogPatternContext(
        project_root=project_root,
        pattern_root=layout.current_recipes_root(),
        module_path="src/enclosure/features/pattern/catalog",
    )


__all__ = ["load_catalog_context"]
