from __future__ import annotations

import tempfile
import textwrap
import unittest
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch

from enclosure.features.workspace.recipe import application


class WorkspaceRecipeCheckTest(unittest.TestCase):
    def test_packaged_recipe_set_passes_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            project_root.mkdir()

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.check_recipes(
                    recipe_root=Path(
                        files("enclosure").joinpath("resources", "recipes")
                    ),
                    recipe_name=None,
                    target_path=None,
                    variables={},
                )

        self.assertTrue(report.passed(), report.violations)

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

    def test_recipe_check_reports_missing_role_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = Path(temporary_directory) / "recipes"
            project_root.mkdir()
            recipe_root.mkdir()
            _write_recipe(
                recipe_root / "missing-role",
                template_text="ok\n",
                role_line="",
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

        self.assertEqual(("invalid_manifest",), tuple(
            violation.code for violation in report.violations
        ))
        self.assertIn("Field required", report.violations[0].message)

    def test_recipe_check_reports_invalid_role_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = Path(temporary_directory) / "recipes"
            project_root.mkdir()
            recipe_root.mkdir()
            _write_recipe(
                recipe_root / "bad-role",
                template_text="ok\n",
                role_line="role: unknown",
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

        self.assertEqual(("invalid_manifest",), tuple(
            violation.code for violation in report.violations
        ))
        self.assertIn("Input should be", report.violations[0].message)

    def test_container_reports_missing_role_recipe(self) -> None:
        report = _check_recipe_root(
            {
                "container": _recipe_manifest(
                    role="container",
                    roles_map={"feature/module": "missing"},
                    content="ok\n",
                )
            }
        )

        self.assertEqual(("missing_role_recipe",), tuple(
            violation.code for violation in report.violations
        ))

    def test_container_reports_non_archetype_role(self) -> None:
        report = _check_recipe_root(
            {
                "container": _recipe_manifest(
                    role="container",
                    roles_map={"feature/module": "other"},
                    content="ok\n",
                ),
                "other": _recipe_manifest(role="container", content="ok\n"),
            }
        )

        self.assertEqual(("non_archetype_role",), tuple(
            violation.code
            for violation in report.violations
            if violation.recipe_name == "container"
        ))

    def test_container_passes_when_roles_map_references_archetype(self) -> None:
        report = _check_recipe_root(
            {
                "container": _recipe_manifest(
                    role="container",
                    roles_map={"feature/module": "part"},
                    content="same\n",
                ),
                "part": _recipe_manifest(role="archetype", content="same\n"),
            }
        )

        self.assertTrue(report.passed())

    def test_recipe_drifts_compare_mapped_module_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = project_root / ".enclosure" / "recipes"
            module_path = project_root / "src" / "features" / "feature" / "module"
            module_path.mkdir(parents=True)
            recipe_root.mkdir(parents=True)
            (module_path / "__init__.py").write_text("", encoding="utf-8")
            (module_path / "extra.py").write_text("", encoding="utf-8")
            _write_recipe_files(
                recipe_root,
                {
                    "container": _recipe_manifest(
                        role="container",
                        roles_map={"other/module": "role"},
                        content="",
                    ),
                    "role": _recipe_manifest(role="archetype", content=""),
                },
            )
            _write_config(project_root, roles_map={"feature/module": "role"})

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.check_recipe_drifts(recipe_root=recipe_root)

        self.assertEqual(1, report.modules_checked)
        self.assertEqual(("sample.py",), report.drifts[0].missing_files)
        self.assertEqual(("__init__.py", "extra.py"), report.drifts[0].extra_files)


def _write_recipe(
    recipe_path: Path,
    *,
    template_text: str,
    role_line: str = "role: archetype",
) -> None:
    recipe_path.mkdir()
    (recipe_path / "recipe.yaml").write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            {role_line}
            files:
              - source: template.py.tmpl
                target: "{{{{ target.path }}}}/sample.py"
            """
        ).strip(),
        encoding="utf-8",
    )
    (recipe_path / "template.py.tmpl").write_text(template_text, encoding="utf-8")


def _check_recipe_root(
    recipe_specs: dict[str, tuple[str, str]],
) -> application.RecipeCheckReport:
    with tempfile.TemporaryDirectory() as temporary_directory:
        project_root = Path(temporary_directory) / "project"
        recipe_root = Path(temporary_directory) / "recipes"
        project_root.mkdir()
        recipe_root.mkdir()
        _write_recipe_files(recipe_root, recipe_specs)

        with patch.object(
            application.layout,
            "current_project_root",
            return_value=project_root,
        ):
            return application.check_recipes(
                recipe_root=recipe_root,
                recipe_name=None,
                target_path=Path("generated"),
                variables={},
            )


def _recipe_manifest(
    *,
    role: str,
    content: str,
    roles_map: dict[str, str] | None = None,
) -> tuple[str, str]:
    manifest_lines = [
        "schema_version: 1",
        f"role: {role}",
    ]
    if roles_map:
        manifest_lines.append("roles_map:")
        manifest_lines.extend(
            f"  {module_name}: {role_name}"
            for module_name, role_name in roles_map.items()
        )
    manifest_lines.extend(
        (
            "files:",
            "  - source: template.py.tmpl",
            '    target: "{{ target.path }}/sample.py"',
        )
    )
    return (
        "\n".join(manifest_lines),
        content,
    )


def _write_recipe_files(
    recipe_root: Path,
    recipe_specs: dict[str, tuple[str, str]],
) -> None:
    for recipe_name, (manifest_text, template_text) in recipe_specs.items():
        recipe_path = recipe_root / recipe_name
        recipe_path.mkdir()
        (recipe_path / "recipe.yaml").write_text(
            manifest_text,
            encoding="utf-8",
        )
        (recipe_path / "template.py.tmpl").write_text(
            template_text,
            encoding="utf-8",
        )


def _write_config(
    project_root: Path,
    *,
    roles_map: dict[str, str] | None = None,
) -> None:
    config_dir = project_root / ".enclosure"
    config_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "architecture:",
        "  root: src/features",
        "workspace:",
        "  recipe:",
        "    skip: []",
    ]
    if roles_map:
        lines.append("    roles_map:")
        lines.extend(
            f"      {module_name}: {role_name}"
            for module_name, role_name in roles_map.items()
        )
    (config_dir / "enclosure.yaml").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
