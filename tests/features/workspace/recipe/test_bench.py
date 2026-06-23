from __future__ import annotations

from pathlib import Path

import enclosure.features.workspace.recipe as recipe
from enclosure.features.workspace.recipe.ui import bench_html


RECIPE_ROOT = Path(".enclosure/recipes")


def test_bench_preview_returns_selected_module_and_html() -> None:
    report = recipe.bench_preview("workspace/recipe", recipe_root=RECIPE_ROOT)

    assert report.passed()
    assert report.selected.module_name == "workspace/recipe"
    assert report.subject_root == report.architecture_root
    assert "workspace/recipe" in bench_html.render_bench_html(report)


def test_bench_all_preview_preserves_existing_workspace_findings() -> None:
    report = recipe.bench_all_preview(recipe_root=RECIPE_ROOT)

    assert report.subject_root == report.architecture_root
    assert report.classification == "unstable"
    assert not report.violations
    assert "Workspace Warp Index" in bench_html.render_bench_all_html(report)
