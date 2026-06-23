from __future__ import annotations

from pathlib import Path

import enclosure.features.workspace.recipe as recipe


RECIPE_ROOT = Path(".enclosure/recipes")


def test_describe_recipe_generation_preserves_preview_file_shapes() -> None:
    report = recipe.describe_recipe_generation(
        "module-workspace-cli",
        "src/orders/reporting/example",
        recipe_root=RECIPE_ROOT,
        variables={},
    )

    assert report["recipe_found"]
    assert not report["recipe_empty"]
    assert report["create_paths"]
    assert report["preview_files"]
    assert {
        preview_file.relative_path.as_posix()
        for preview_file in report["preview_files"]
    } >= {
        "src/orders/reporting/example/application/commands.py",
        "src/orders/reporting/example/application/queries.py",
    }
