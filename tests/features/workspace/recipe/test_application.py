from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from enclosure.features.workspace.recipe import application


class WorkspaceRecipeCheckTest(unittest.TestCase):
    def test_all_recipe_check_renders_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = Path(temporary_directory) / "recipes"
            project_root.mkdir()
            recipe_root.mkdir()
            _write_recipe(
                recipe_root / "ok",
                template_text="class {{ target.class }}:\n    pass\n",
            )
            _write_recipe(
                recipe_root / "broken",
                template_text="{{ missing.value }}\n",
            )

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.check_recipes(
                    recipe_root=recipe_root,
                    recipe_name=None,
                    target_path=None,
                    variables={},
                )

        self.assertEqual(2, report.recipes_checked)
        self.assertEqual(1, report.rendered_paths_checked)
        self.assertEqual(("broken",), tuple(
            violation.recipe_name for violation in report.violations
        ))
        self.assertEqual(("render_failed",), tuple(
            violation.code for violation in report.violations
        ))


def _write_recipe(recipe_path: Path, *, template_text: str) -> None:
    recipe_path.mkdir()
    (recipe_path / "recipe.yaml").write_text(
        textwrap.dedent(
            """
            schema_version: 1
            files:
              - source: template.py.tmpl
                target: "{{ target.path }}/sample.py"
            """
        ).strip(),
        encoding="utf-8",
    )
    (recipe_path / "template.py.tmpl").write_text(template_text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
