from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from enclosure.features.workspace.recipe import application
from enclosure.shared import layout


class ConfigNode(SimpleNamespace):
    pass


class TestSettings:
    @property
    def metadata(self) -> SimpleNamespace:
        return SimpleNamespace(project_root=application.layout.current_project_root())

    def query(self, path: str) -> object:
        config_path = application.layout.current_project_root() / ".enclosure" / "enclosure.yaml"
        value: object = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        for part in tuple(part.strip() for part in path.split(".") if part.strip()):
            value = value[part]
        return _config_object(value)


def _config_object(value: object) -> object:
    if isinstance(value, dict):
        return ConfigNode(
            **{
                key: item if key == "roles_map" else _config_object(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list):
        return tuple(_config_object(item) for item in value)
    return value


application.layout = SimpleNamespace(current_project_root=lambda: Path.cwd())
application.settings = TestSettings()


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

    def test_recipe_dry_run_includes_rendered_preview_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = Path(temporary_directory) / "recipes"
            project_root.mkdir()
            recipe_root.mkdir()
            _write_config(project_root)
            _write_recipe(
                recipe_root / "role",
                template_text="class {{ target.class }}:\n    pass\n",
            )

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.describe_recipe_generation(
                    "role",
                    "generated",
                    recipe_root=recipe_root,
                    variables={},
                )

        expected_project_root = project_root.resolve()
        self.assertEqual(
            (expected_project_root / "generated" / "sample.py",),
            report["create_paths"],
        )
        self.assertEqual((), report["skipped_paths"])
        self.assertEqual(1, len(report["preview_files"]))
        preview_file = report["preview_files"][0]
        self.assertEqual(
            recipe_root / "role" / "template.py.tmpl",
            preview_file.source_path,
        )
        self.assertEqual(
            expected_project_root / "generated" / "sample.py",
            preview_file.target_path,
        )
        self.assertEqual("generated/sample.py", preview_file.relative_path.as_posix())
        self.assertEqual(application.RecipePreviewStatus.CREATE, preview_file.status)
        self.assertEqual("class Generated:\n    pass\n", preview_file.content)

    def test_recipe_dry_run_preview_marks_existing_targets_as_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = Path(temporary_directory) / "recipes"
            generated_file = project_root / "generated" / "sample.py"
            project_root.mkdir()
            recipe_root.mkdir()
            generated_file.parent.mkdir(parents=True)
            generated_file.write_text("existing\n", encoding="utf-8")
            _write_config(project_root)
            _write_recipe(recipe_root / "role", template_text="new\n")

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.describe_recipe_generation(
                    "role",
                    "generated",
                    recipe_root=recipe_root,
                    variables={},
                )

        self.assertEqual((), report["create_paths"])
        self.assertEqual((generated_file.resolve(),), report["skipped_paths"])
        self.assertEqual(
            application.RecipePreviewStatus.SKIP_EXISTS,
            report["preview_files"][0].status,
        )
        self.assertEqual("new\n", report["preview_files"][0].content)

    def test_recipe_dry_run_preview_marks_config_skips(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            recipe_root = Path(temporary_directory) / "recipes"
            project_root.mkdir()
            recipe_root.mkdir()
            _write_config(project_root, skip=("generated/sample.py",))
            _write_recipe(recipe_root / "role", template_text="skipped\n")

            with patch.object(
                application.layout,
                "current_project_root",
                return_value=project_root,
            ):
                report = application.describe_recipe_generation(
                    "role",
                    "generated",
                    recipe_root=recipe_root,
                    variables={},
                )

        self.assertEqual((), report["create_paths"])
        self.assertEqual(
            (project_root.resolve() / "generated" / "sample.py",),
            report["skipped_paths"],
        )
        self.assertEqual(
            application.RecipePreviewStatus.SKIP_CONFIG,
            report["preview_files"][0].status,
        )
        self.assertEqual("skipped\n", report["preview_files"][0].content)

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

    def test_recipe_bench_reports_unmapped_module(self) -> None:
        report = _bench_preview(
            selected_module="feature/missing",
            roles_map={"feature/module": "role"},
            actual_files_by_module={"feature/module": ("sample.py",)},
        )

        self.assertEqual(("module_unmapped",), tuple(
            violation.code for violation in report.violations
        ))

    def test_recipe_bench_reports_no_residue_for_matching_modules(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
            },
            actual_files_by_module={
                "feature/module": ("sample.py",),
                "feature/peer": ("sample.py",),
            },
        )

        self.assertTrue(report.passed())
        self.assertEqual(2, report.same_role_module_count)
        self.assertEqual(0, report.local_residue_count)
        self.assertEqual(0, report.local_slot_growth_count)
        self.assertEqual(0, report.local_content_weight_count)
        self.assertEqual(0, report.local_warp_count)
        self.assertEqual("clean", report.classification)
        self.assertEqual((), report.recurrence)
        self.assertEqual(("sample.py",), report.selected.actual_files)
        self.assertEqual(("sample.py",), report.selected.expected_files)

    def test_recipe_bench_reports_unique_local_residue(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
            },
            actual_files_by_module={
                "feature/module": ("sample.py", "unique.py"),
                "feature/peer": ("sample.py",),
            },
        )

        self.assertEqual(("unique.py",), report.selected.residue_files)
        self.assertEqual("local", report.classification)
        self.assertEqual(1, report.recurrence[0].count)
        self.assertEqual("local", report.recurrence[0].label)

    def test_recipe_bench_counts_package_internals_as_slot_growth(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
            },
            actual_files_by_module={
                "feature/module": ("sample/__init__.py", "sample/private.py"),
                "feature/peer": ("sample/__init__.py",),
            },
            recipes={
                "module": _container_manifest({"role": "role"}),
                "role": _slot_manifest(
                    slot_lines=("    sample: package",),
                    targets=("{{ target.path }}/sample/__init__.py",),
                ),
            },
        )

        self.assertEqual((), report.selected.residue_files)
        self.assertEqual(("sample/private.py",), report.selected.slot_growth_files)
        self.assertEqual(1, report.local_slot_growth_count)
        self.assertEqual("local", report.classification)

    def test_recipe_bench_reports_content_weight_for_large_files(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={"feature/module": "role"},
            actual_files_by_module={"feature/module": ("sample.py",)},
            content_by_file={
                "feature/module/sample.py": "\n".join("value" for _index in range(300)),
            },
        )

        self.assertEqual(1, report.local_content_weight_count)
        self.assertEqual("sample.py", report.selected.content_weights[0].path)
        self.assertIn("300 lines", report.selected.content_weights[0].reason)
        self.assertEqual(0, report.selected.content_weights[0].symbol_count)
        self.assertEqual("local", report.classification)

    def test_recipe_bench_reports_content_weight_for_non_python_files(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={"feature/module": "role"},
            actual_files_by_module={"feature/module": ("sample.ts",)},
            content_by_file={
                "feature/module/sample.ts": "\n".join(
                    "export const value = 1;" for _index in range(300)
                ),
            },
        )

        self.assertEqual(1, report.local_content_weight_count)
        self.assertEqual("sample.ts", report.selected.content_weights[0].path)
        self.assertIn("300 lines", report.selected.content_weights[0].reason)
        self.assertEqual(0, report.selected.content_weights[0].symbol_count)
        self.assertEqual("local", report.classification)

    def test_recipe_bench_counts_same_role_recurrence_and_excludes_other_roles(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
                "feature/other": "other",
            },
            actual_files_by_module={
                "feature/module": ("sample.py", "common.py"),
                "feature/peer": ("sample.py", "common.py"),
                "feature/other": ("sample.py", "common.py"),
            },
            recipes={
                "module": _container_manifest({"role": "role", "other": "other"}),
                "role": _recipe_manifest(role="archetype", content=""),
                "other": _recipe_manifest(role="archetype", content=""),
            },
        )

        self.assertEqual(2, report.same_role_module_count)
        self.assertEqual(("common.py",), report.selected.residue_files)
        self.assertEqual(1, report.repeated_residue_count)
        self.assertEqual(2, report.recurrence[0].count)
        self.assertEqual(("feature/module", "feature/peer"), report.recurrence[0].modules)

    def test_recipe_bench_uses_configured_skip_for_actual_files(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={"feature/module": "role"},
            actual_files_by_module={
                "feature/module": ("sample.py", "cache/generated.tmp"),
            },
            skip=("cache/**",),
        )

        self.assertEqual(("sample.py",), report.selected.actual_files)
        self.assertEqual((), report.selected.residue_files)
        self.assertEqual((), report.selected.slot_growth_files)

    def test_recipe_bench_html_contains_visual_sections(self) -> None:
        report = _bench_preview(
            selected_module="feature/module",
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
            },
            actual_files_by_module={
                "feature/module": ("sample.py", "common.py"),
                "feature/peer": ("sample.py", "common.py"),
            },
            content_by_file={
                "feature/module/common.py": "def smell():\n    return True\n",
            },
        )

        html_report = application.render_recipe_bench_html(report)

        self.assertIn("Bench Preview Warp Report", html_report)
        self.assertIn("Actual Tree", html_report)
        self.assertIn("Recipe Expected", html_report)
        self.assertIn("Forbidden Residue", html_report)
        self.assertIn("Slot Growth", html_report)
        self.assertIn("Content Weight", html_report)
        self.assertIn("Same-Role Matrix", html_report)
        self.assertIn("Recurrence", html_report)
        self.assertIn("feature/module", html_report)
        self.assertIn("common.py", html_report)
        self.assertIn("2/2 <span class=\"badge severity-high\">established</span>", html_report)
        self.assertIn("badge severity-high", html_report)
        self.assertIn("severity-card severity-high", html_report)
        self.assertIn("def smell()", html_report)

    def test_recipe_bench_all_reports_workspace_warp_index(self) -> None:
        report = _bench_all_preview(
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
                "feature/other": "other",
            },
            actual_files_by_module={
                "feature/module": ("sample.py", "common.py"),
                "feature/peer": ("sample.py", "common.py"),
                "feature/other": ("sample.py", "local.py"),
            },
            recipes={
                "module": _container_manifest({"role": "role", "other": "other"}),
                "role": _recipe_manifest(role="archetype", content=""),
                "other": _recipe_manifest(role="archetype", content=""),
            },
        )

        self.assertTrue(report.passed())
        self.assertEqual(3, report.module_count)
        self.assertEqual(2, report.role_count)
        self.assertEqual(3, report.reports_with_residue_count)
        self.assertEqual(3, report.reports_with_warp_count)
        self.assertEqual(3, report.local_residue_count)
        self.assertEqual(2, report.repeated_residue_count)
        self.assertEqual(3, report.local_warp_count)
        self.assertEqual("established", report.classification)

    def test_recipe_bench_all_html_contains_workspace_sections(self) -> None:
        report = _bench_all_preview(
            roles_map={
                "feature/module": "role",
                "feature/peer": "role",
            },
            actual_files_by_module={
                "feature/module": ("sample.py", "common.py"),
                "feature/peer": ("sample.py", "common.py"),
            },
        )

        html_report = application.render_recipe_bench_all_html(report)

        self.assertIn("Workspace Warp Index", html_report)
        self.assertIn("Module Index", html_report)
        self.assertIn("Roles", html_report)
        self.assertIn("feature/module", html_report)
        self.assertIn("feature/peer", html_report)
        self.assertIn("common.py", html_report)
        self.assertIn("2/2 <span class=\"badge severity-high\">established</span>", html_report)
        self.assertIn("severity-row severity-high", html_report)
        self.assertIn("severity-bar severity-high", html_report)


def _write_recipe(
    recipe_path: Path,
    *,
    template_text: str,
    role_line: str = "role: archetype",
) -> None:
    recipe_path.mkdir()
    layout.recipe_manifest_path(recipe_path).write_text(
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


def _bench_preview(
    *,
    selected_module: str,
    roles_map: dict[str, str],
    actual_files_by_module: dict[str, tuple[str, ...]],
    recipes: dict[str, tuple[str, str]] | None = None,
    skip: tuple[str, ...] = (),
    content_by_file: dict[str, str] | None = None,
) -> application.RecipeBenchReport:
    with tempfile.TemporaryDirectory() as temporary_directory:
        project_root = Path(temporary_directory) / "project"
        recipe_root = project_root / ".enclosure" / "recipes"
        project_root.mkdir()
        recipe_root.mkdir(parents=True)
        for module_name, actual_files in actual_files_by_module.items():
            module_path = project_root / "src" / "features" / module_name
            module_path.mkdir(parents=True)
            for actual_file in actual_files:
                actual_path = module_path / actual_file
                actual_path.parent.mkdir(parents=True, exist_ok=True)
                actual_path.write_text(
                    (content_by_file or {}).get(
                        f"{module_name}/{actual_file}",
                        "",
                    ),
                    encoding="utf-8",
                )
        _write_recipe_files(
            recipe_root,
            recipes
            if recipes is not None
            else {
                "module": _container_manifest({"role": "role"}),
                "role": _recipe_manifest(role="archetype", content=""),
            },
        )
        _write_config(project_root, roles_map=roles_map, skip=skip)

        with patch.object(
            application.layout,
            "current_project_root",
            return_value=project_root,
        ):
            return application.bench_preview(
                selected_module,
                recipe_root=recipe_root,
            )


def _bench_all_preview(
    *,
    roles_map: dict[str, str],
    actual_files_by_module: dict[str, tuple[str, ...]],
    recipes: dict[str, tuple[str, str]] | None = None,
    skip: tuple[str, ...] = (),
) -> application.RecipeBenchAllReport:
    with tempfile.TemporaryDirectory() as temporary_directory:
        project_root = Path(temporary_directory) / "project"
        recipe_root = project_root / ".enclosure" / "recipes"
        project_root.mkdir()
        recipe_root.mkdir(parents=True)
        for module_name, actual_files in actual_files_by_module.items():
            module_path = project_root / "src" / "features" / module_name
            module_path.mkdir(parents=True)
            for actual_file in actual_files:
                actual_path = module_path / actual_file
                actual_path.parent.mkdir(parents=True, exist_ok=True)
                actual_path.write_text("", encoding="utf-8")
        _write_recipe_files(
            recipe_root,
            recipes
            if recipes is not None
            else {
                "module": _container_manifest({"role": "role"}),
                "role": _recipe_manifest(role="archetype", content=""),
            },
        )
        _write_config(project_root, roles_map=roles_map, skip=skip)

        with patch.object(
            application.layout,
            "current_project_root",
            return_value=project_root,
        ):
            return application.bench_all_preview(recipe_root=recipe_root)


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
        layout.recipe_manifest_path(recipe_path).write_text(
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
