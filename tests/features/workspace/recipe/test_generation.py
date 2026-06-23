from __future__ import annotations

from pathlib import Path

import enclosure.features.workspace.recipe as recipe


RECIPE_ROOT = Path(".enclosure/recipes")


def test_describe_recipe_generation_preserves_preview_file_shapes(
    configured_recipe_names: tuple[str, ...],
) -> None:
    recipe_name = configured_recipe_names[0]
    target_path = "src/orders/reporting/example"
    report = recipe.describe_recipe_generation(
        recipe_name,
        target_path,
        recipe_root=RECIPE_ROOT,
        variables={},
    )

    assert report["recipe_found"]
    assert not report["recipe_empty"]
    assert report["create_paths"]
    assert report["preview_files"]
    assert all(
        preview_file.relative_path.as_posix().startswith(target_path)
        for preview_file in report["preview_files"]
    )


def test_reusable_recipe_rendered_files_do_not_import_enclosure_shared(
    configured_recipe_names: tuple[str, ...],
) -> None:
    forbidden_imports = (
        "enclosure.shared",
        "enclosure.shared.config",
        "enclosure.shared.scaffolding",
    )

    for recipe_name in configured_recipe_names:
        report = recipe.describe_recipe_generation(
            recipe_name,
            f"src/orders/{recipe_name.replace('-', '_')}",
            recipe_root=RECIPE_ROOT,
            variables={},
        )

        assert report["recipe_found"], recipe_name
        for preview_file in report["preview_files"]:
            for forbidden_import in forbidden_imports:
                assert forbidden_import not in preview_file.content, (
                    recipe_name,
                    preview_file.relative_path.as_posix(),
                    forbidden_import,
                )
