from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from enclosure.features.workspace.recipe import application


class WorkspaceRecipeCheckTest(unittest.TestCase):
    def test_missing_recipe_root_reports_missing_container(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            project_root.mkdir()
            _write_config(project_root, roles_map={"feature/module": "role"})

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.check_recipes(
                    recipe_root=Path(temporary_directory) / "missing-recipes",
                    recipe_name=None,
                    target_path=None,
                    variables={},
                )

        self.assertEqual(0, report.recipes_discovered)
        self.assertIn("missing_container", tuple(
            violation.code for violation in report.violations
        ))

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
            _write_recipe_files(
                recipe_root,
                {"module": _container_manifest({"ok": "ok", "broken": "broken"})},
            )
            _write_config(project_root, roles_map={"feature/module": "ok"})

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

        self.assertEqual(3, report.recipes_checked)
        self.assertEqual(2, report.rendered_paths_checked)
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
            _write_config(project_root, roles_map={"feature/module": "missing-role"})
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
            _write_config(project_root, roles_map={"feature/module": "bad-role"})
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

    def test_catalog_reports_missing_container(self) -> None:
        report = _check_recipe_root(
            {
                "role": _recipe_manifest(role="archetype", content="ok\n"),
            }
        )

        self.assertEqual(("missing_container",), tuple(
            violation.code for violation in report.violations
        ))

    def test_container_reports_missing_archetype_recipe(self) -> None:
        report = _check_recipe_root(
            {
                "module": _container_manifest({"missing": "missing"}),
            },
            roles_map={"feature/module": "module"},
        )

        self.assertEqual(("missing_archetype_recipe", "non_archetype_role_recipe"), tuple(
            violation.code for violation in report.violations
        ))

    def test_catalog_reports_multiple_containers(self) -> None:
        report = _check_recipe_root(
            {
                "module": _container_manifest({}),
                "other": _container_manifest({}),
            },
            roles_map={"feature/module": "module"},
        )

        self.assertEqual(("multiple_containers", "non_archetype_role_recipe"), tuple(
            violation.code for violation in report.violations
        ))

    def test_archetype_reports_unexpected_roles_map(self) -> None:
        report = _check_recipe_root(
            {
                "module": _container_manifest({"role": "role"}),
                "role": _recipe_manifest(
                    role="archetype",
                    roles_map={"feature/module": "other"},
                    content="ok\n",
                )
            },
            roles_map={"feature/module": "role"},
        )

        self.assertEqual(("unexpected_roles_map",), tuple(
            violation.code for violation in report.violations
        ))

    def test_archetype_reports_missing_ladder_metadata(self) -> None:
        report = _check_recipe_root(
            {
                "module": _container_manifest({"role": "role"}),
                "role": _recipe_manifest(
                    role="archetype",
                    content="ok\n",
                    include_ladder=False,
                ),
            },
            roles_map={"feature/module": "role"},
        )

        self.assertEqual(("missing_ladder",), tuple(
            violation.code for violation in report.violations
        ))

    def test_recipe_check_reports_invalid_ladder_state(self) -> None:
        report = _check_recipe_root(
            {
                "module": _container_manifest({"role": "role"}),
                "role": _recipe_manifest(
                    role="archetype",
                    content="ok\n",
                    ladder_lines=(
                        "ladder:",
                        "  family: module",
                        "  rung: broken",
                        "  slots:",
                        "    sample: directory",
                    ),
                ),
            },
            roles_map={"feature/module": "role"},
        )

        self.assertEqual(("invalid_manifest",), tuple(
            violation.code for violation in report.violations
        ))
        self.assertIn("Unsupported recipe ladder state", report.violations[0].message)

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
                    "module": _container_manifest({"role": "role"}),
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
        self.assertEqual("module", report.drifts[0].ladder_family)
        self.assertEqual("sample", report.drifts[0].ladder_rung)
        self.assertEqual(("sample.py",), report.drifts[0].missing_files)
        self.assertEqual(("__init__.py", "extra.py"), report.drifts[0].extra_files)

    def test_recipe_drifts_allow_package_slot_internals(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=(
                    "    sample: package",
                    "    ui: package",
                ),
                targets=(
                    "{{ target.path }}/sample/__init__.py",
                    "{{ target.path }}/ui/__init__.py",
                ),
            ),
            actual_files=(
                "__init__.py",
                "sample/__init__.py",
                "sample/private.py",
                "ui/__init__.py",
                "ui/templates/report.tmpl",
            ),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual((), report.drifts[0].extra_files)

    def test_recipe_drifts_compose_role_from_fixed_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = project_root / ".enclosure" / "recipes"
            module_path = project_root / "src" / "features" / "feature" / "module"
            module_path.mkdir(parents=True)
            recipe_root.mkdir(parents=True)
            (module_path / "__init__.py").write_text("", encoding="utf-8")
            (module_path / "sample.py").write_text("", encoding="utf-8")
            (module_path / "support.py").write_text("", encoding="utf-8")
            _write_recipe_files(
                recipe_root,
                {
                    "module": _container_manifest({"base": "base"}),
                    "base": _recipe_manifest(role="archetype", content=""),
                    "support": _slot_manifest(
                        role="fragment",
                        slot_lines=("    support: file",),
                        targets=("{{ target.path }}/support.py",),
                    ),
                },
            )
            _write_config(
                project_root,
                roles_map={"feature/module": "base+support"},
            )

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.check_recipe_drifts(recipe_root=recipe_root)

        self.assertEqual(1, report.modules_checked)
        self.assertEqual((), report.violations)
        self.assertEqual("composed", report.drifts[0].ladder_family)
        self.assertEqual("base+support", report.drifts[0].ladder_rung)
        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual((), report.drifts[0].extra_files)

    def test_recipe_drifts_report_file_and_package_conflict(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=("    sample: file",),
                targets=("{{ target.path }}/sample.py",),
            ),
            actual_files=(
                "__init__.py",
                "sample.py",
                "sample/__init__.py",
            ),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual(("sample/__init__.py",), report.drifts[0].extra_files)

    def test_recipe_drifts_report_missing_package_seam(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=("    sample: package",),
                targets=("{{ target.path }}/sample/__init__.py",),
            ),
            actual_files=("__init__.py", "sample/private.py"),
        )

        self.assertEqual(("sample/__init__.py",), report.drifts[0].missing_files)
        self.assertEqual((), report.drifts[0].extra_files)

    def test_recipe_drifts_use_rendered_file_extension_for_file_slots(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=("    sample: file",),
                root_target="{{ target.path }}/index.ts",
                targets=("{{ target.path }}/sample.ts",),
            ),
            actual_files=("index.ts", "sample.ts"),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual((), report.drifts[0].extra_files)

    def test_recipe_drifts_use_rendered_package_seam_for_package_slots(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=("    sample: package",),
                root_target="{{ target.path }}/index.ts",
                targets=("{{ target.path }}/sample/index.ts",),
            ),
            actual_files=(
                "index.ts",
                "sample.ts",
                "sample/index.ts",
                "sample/private.ts",
            ),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual(("sample.ts",), report.drifts[0].extra_files)

    def test_recipe_drifts_use_configured_skip_for_actual_files(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=("    sample: file",),
                root_target="{{ target.path }}/index.ts",
                targets=("{{ target.path }}/sample.ts",),
            ),
            actual_files=(
                "index.ts",
                "sample.ts",
                "cache/generated.tmp",
            ),
            skip=("cache/**",),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual((), report.drifts[0].extra_files)

    def test_recipe_drifts_report_root_extra_outside_slots(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=("    sample: package",),
                targets=("{{ target.path }}/sample/__init__.py",),
            ),
            actual_files=(
                "__init__.py",
                "sample/__init__.py",
                "other.py",
            ),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual(("other.py",), report.drifts[0].extra_files)

    def test_recipe_drifts_check_split_file_slots(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=(
                    "    application:",
                    "      state: split-files",
                    "      files:",
                    "        - commands.py",
                    "        - queries.py",
                ),
                targets=(
                    "{{ target.path }}/application/__init__.py",
                    "{{ target.path }}/application/commands.py",
                    "{{ target.path }}/application/queries.py",
                ),
            ),
            actual_files=(
                "__init__.py",
                "application/__init__.py",
                "application/commands.py",
                "application/queries.py",
                "application/commands/__init__.py",
            ),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual(("application/commands/__init__.py",), report.drifts[0].extra_files)

    def test_recipe_drifts_check_split_package_slots(self) -> None:
        report = _check_ladder_drift(
            manifest=_slot_manifest(
                slot_lines=(
                    "    application:",
                    "      state: split-packages",
                    "      packages:",
                    "        - commands",
                    "        - queries",
                ),
                targets=(
                    "{{ target.path }}/application/__init__.py",
                    "{{ target.path }}/application/commands/__init__.py",
                    "{{ target.path }}/application/queries/__init__.py",
                ),
            ),
            actual_files=(
                "__init__.py",
                "application/__init__.py",
                "application/commands.py",
                "application/commands/__init__.py",
                "application/queries/__init__.py",
            ),
        )

        self.assertEqual((), report.drifts[0].missing_files)
        self.assertEqual(("application/commands.py",), report.drifts[0].extra_files)

    def test_recipe_drifts_report_missing_config_roles_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = project_root / ".enclosure" / "recipes"
            project_root.mkdir()
            recipe_root.mkdir(parents=True)
            _write_recipe_files(
                recipe_root,
                {
                    "module": _container_manifest({"role": "role"}),
                    "role": _recipe_manifest(role="archetype", content=""),
                },
            )
            _write_config(project_root, roles_map={})

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.check_recipe_drifts(recipe_root=recipe_root)

        self.assertEqual(("missing_roles_map",), tuple(
            violation.code for violation in report.violations
        ))


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
            ladder:
              family: module
              rung: sample
              slots:
                sample: file
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
    *,
    roles_map: dict[str, str] | None = None,
) -> application.RecipeCheckReport:
    with tempfile.TemporaryDirectory() as temporary_directory:
        project_root = Path(temporary_directory) / "project"
        recipe_root = Path(temporary_directory) / "recipes"
        project_root.mkdir()
        recipe_root.mkdir()
        _write_recipe_files(recipe_root, recipe_specs)
        _write_config(
            project_root,
            roles_map=roles_map
            if roles_map is not None
            else {"feature/module": "role"},
        )

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
    include_ladder: bool = True,
    ladder_lines: tuple[str, ...] = (),
) -> tuple[str, str]:
    manifest_lines = [
        "schema_version: 1",
        f"role: {role}",
    ]
    if include_ladder:
        manifest_lines.extend(
            ladder_lines
            if ladder_lines
            else (
                "ladder:",
                "  family: module",
                "  rung: sample",
                "  slots:",
                "    sample: file",
            )
        )
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


def _slot_manifest(
    *,
    role: str = "archetype",
    slot_lines: tuple[str, ...],
    targets: tuple[str, ...],
    root_target: str = "{{ target.path }}/__init__.py",
) -> tuple[str, str]:
    manifest_lines = [
        "schema_version: 1",
        f"role: {role}",
        "ladder:",
        "  family: module",
        "  rung: sample",
        "  slots:",
    ]
    manifest_lines.extend(slot_lines)
    manifest_lines.append("files:")
    manifest_lines.extend(
        (
            "  - source: template.py.tmpl",
            f'    target: "{root_target}"',
        )
    )
    for target in targets:
        manifest_lines.extend(
            (
                "  - source: template.py.tmpl",
                f'    target: "{target}"',
            )
        )
    return ("\n".join(manifest_lines), "")


def _check_ladder_drift(
    *,
    manifest: tuple[str, str],
    actual_files: tuple[str, ...],
    skip: tuple[str, ...] = (),
) -> application.RecipeDriftReport:
    with tempfile.TemporaryDirectory() as temporary_directory:
        project_root = Path(temporary_directory) / "project"
        recipe_root = project_root / ".enclosure" / "recipes"
        module_path = project_root / "src" / "features" / "feature" / "module"
        module_path.mkdir(parents=True)
        recipe_root.mkdir(parents=True)
        for actual_file in actual_files:
            actual_path = module_path / actual_file
            actual_path.parent.mkdir(parents=True, exist_ok=True)
            actual_path.write_text("", encoding="utf-8")
        _write_recipe_files(
            recipe_root,
            {
                "module": _container_manifest({"role": "role"}),
                "role": manifest,
            },
        )
        _write_config(project_root, roles_map={"feature/module": "role"}, skip=skip)

        with patch.object(
            application.layout,
            "current_project_root",
            return_value=project_root,
        ):
            return application.check_recipe_drifts(recipe_root=recipe_root)


def _container_manifest(roles_map: dict[str, str] | None = None) -> tuple[str, str]:
    manifest_lines = [
        "schema_version: 1",
        "role: container",
    ]
    if roles_map:
        manifest_lines.append("archetypes:")
        manifest_lines.extend(
            f"  - {recipe_name}"
            for recipe_name in roles_map.values()
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
        "",
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
    skip: tuple[str, ...] = (),
) -> None:
    config_dir = project_root / ".enclosure"
    config_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "architecture:",
        "  root: src/features",
        "workspace:",
        "  recipe:",
    ]
    if skip:
        lines.append("    skip:")
        lines.extend(f"      - {skip_glob}" for skip_glob in skip)
    else:
        lines.append("    skip: []")
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
