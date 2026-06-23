from __future__ import annotations

from pathlib import Path

import enclosure.features.workspace.recipe as recipe


RECIPE_ROOT = Path(".enclosure/recipes")


def test_package_facade_lists_shows_and_checks_real_recipe_catalog() -> None:
    recipes = recipe.list_recipes(recipe_root=RECIPE_ROOT)

    assert "module-workspace-cli" in {item["name"] for item in recipes}
    assert recipe.show_recipe(
        "module-workspace-cli",
        recipe_root=RECIPE_ROOT,
    )["role"] == "archetype"

    report = recipe.check_recipes(
        recipe_root=RECIPE_ROOT,
        recipe_name=None,
        target_path=None,
        variables={},
    )

    assert report.passed()
    assert report.recipes_checked == len(recipes)
    assert report.rendered_paths_checked > 0
