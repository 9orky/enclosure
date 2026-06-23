from __future__ import annotations

from pathlib import Path

import enclosure.features.workspace.recipe as recipe


RECIPE_ROOT = Path(".enclosure/recipes")
REUSABLE_RECIPE_NAMES = (
    "module",
    "module-config-support",
    "module-domain-package-cli",
    "module-report-cli",
    "module-workspace-cli",
    "pattern-module",
    "slot-infrastructure-file",
)


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


def test_reusable_recipe_rendered_files_do_not_import_enclosure_shared() -> None:
    forbidden_imports = (
        "enclosure.shared",
        "enclosure.shared.config",
        "enclosure.shared.scaffolding",
    )

    for recipe_name in REUSABLE_RECIPE_NAMES:
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
