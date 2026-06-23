from __future__ import annotations

import shutil
from pathlib import Path
from textwrap import dedent

from conftest import copy_fixture, run_cli


def test_recipe_check_reports_missing_catalog_violations(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "clean_architecture")

    result = run_cli(project_root, "workspace", "recipe", "--check")

    assert result.returncode == 1
    assert "Recipe check report." in result.stdout
    assert "Recipes discovered: 0" in result.stdout
    assert "missing_container" in result.stdout
    assert "missing_roles_map" in result.stdout


def test_recipe_check_list_show_and_drift_cover_configured_recipe_mapping(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    check = run_cli(project_root, "workspace", "recipe", "--check")
    list_result = run_cli(project_root, "workspace", "recipe", "--list")
    show = run_cli(project_root, "workspace", "recipe", "compact", "--show")
    drifts = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert check.returncode == 0, check.stderr
    assert "Recipe check passed." in check.stdout
    assert list_result.returncode == 0, list_result.stderr
    assert "- compact (archetype) - Compact fixture module." in list_result.stdout
    assert show.returncode == 0, show.stderr
    assert "Recipe 'compact'." in show.stdout
    assert "{{ target.path }}/application.py" in show.stdout
    assert drifts.returncode == 0, drifts.stderr
    assert "- orders/report: compact (module/compact)" in drifts.stdout
    assert "No recipe drifts found." in drifts.stdout


def test_recipe_dry_run_reports_generated_files_and_content(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "compact",
        "src/enclosure/features/billing/report",
        "--dry-run",
        "--tree",
        "--content",
    )

    assert result.returncode == 0, result.stderr
    assert "Dry run for recipe 'compact'." in result.stdout
    assert "Would create 2 path(s)." in result.stdout
    assert "src/enclosure/features/billing/report/application.py" in result.stdout
    assert "def run():" in result.stdout
    assert not (project_root / "src/enclosure/features/billing/report/application.py").exists()


def test_recipe_bench_commands_write_html_reports_for_mapped_modules(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    bench = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "orders/report",
        "--html",
        ".enclosure/bench.html",
    )
    bench_all = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench-all",
        "--html",
        ".enclosure/index.html",
    )

    assert bench.returncode == 0, bench.stderr
    assert "Bench preview for module 'orders/report'." in bench.stdout
    assert "Classification: clean" in bench.stdout
    assert (project_root / ".enclosure" / "bench.html").is_file()
    assert bench_all.returncode == 0, bench_all.stderr
    assert "Workspace warp index." in bench_all.stdout
    assert "Mapped modules: 1" in bench_all.stdout
    assert (project_root / ".enclosure" / "index.html").is_file()


def test_recipe_check_reports_catalog_role_and_rendering_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "bad_recipe_workspace")

    result = run_cli(project_root, "workspace", "recipe", "--check")

    assert result.returncode == 1
    assert "Recipes discovered: 3" in result.stdout
    assert "multiple_containers" in result.stdout
    assert "missing_role_recipe" in result.stdout
    assert "non_archetype_role_recipe" in result.stdout
    assert "missing_ladder" in result.stdout
    assert "render_failed" in result.stdout


def test_recipe_drifts_report_roles_map_and_missing_module_violations(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "bad_recipe_workspace")

    result = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert result.returncode == 1
    assert "Recipe drift report." in result.stdout
    assert "multiple_containers" in result.stdout
    assert "missing_role_recipe" in result.stdout
    assert "non_archetype_role_recipe" in result.stdout
    assert "mapped_module_missing" in result.stdout


def test_recipe_check_can_validate_single_recipe_with_required_variables(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _write_named_recipe(project_root)

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "named",
        "src/enclosure/features/invoices/report",
        "--check",
        "--var",
        "entity=invoice",
    )

    assert result.returncode == 0, result.stderr
    assert "Recipe check report." in result.stdout
    assert "Recipes discovered: 3" in result.stdout
    assert "Recipes checked: 1" in result.stdout
    assert "Rendered paths checked: 1" in result.stdout
    assert "Recipe check passed." in result.stdout


def test_recipe_check_reports_invalid_required_variable_values(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _write_named_recipe(project_root)

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "named",
        "src/enclosure/features/invoices/report",
        "--check",
        "--var",
        "entity=Not Valid",
    )

    assert result.returncode == 1
    assert "render_failed" in result.stdout
    assert "Scaffold variable entity must be a kebab-case slug" in result.stdout


def test_recipe_command_rejects_malformed_variable_pairs(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "compact",
        "src/enclosure/features/billing/report",
        "--dry-run",
        "--var",
        "missing-separator",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Scaffold variables must use key=value syntax" in result.stderr


def test_recipe_generate_preserves_existing_files_and_honors_skip_config(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {"orders/report": "skip-aware"})
    _write_skip_aware_recipe(project_root)
    existing_file = project_root / "src/enclosure/features/orders/report/application.py"
    existing_content = existing_file.read_text(encoding="utf-8")

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "skip-aware",
        "src/enclosure/features/orders/report",
    )

    assert result.returncode == 0, result.stderr
    assert "Generated recipe 'skip-aware'." in result.stdout
    assert "Created 1 path(s)." in result.stdout
    assert "Skipped 2 path(s)." in result.stdout
    assert existing_file.read_text(encoding="utf-8") == existing_content
    assert (project_root / "src/enclosure/features/orders/report/domain.py").is_file()
    assert not (
        project_root / "src/enclosure/features/orders/report/__pycache__/ignored.py"
    ).exists()


def test_recipe_dry_run_reports_skip_exists_and_skip_config_statuses(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {"orders/report": "skip-aware"})
    _write_skip_aware_recipe(project_root)

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "skip-aware",
        "src/enclosure/features/orders/report",
        "--dry-run",
        "--tree",
    )

    assert result.returncode == 0, result.stderr
    assert "Skipped 2 path(s)." in result.stdout
    assert "[skip_exists] src/enclosure/features/orders/report/application.py" in result.stdout
    assert "[skip_config] src/enclosure/features/orders/report/__pycache__/ignored.py" in result.stdout
    assert "[create] src/enclosure/features/orders/report/domain.py" in result.stdout


def test_recipe_drifts_report_missing_and_extra_files(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    application_file = project_root / "src/enclosure/features/orders/report/application.py"
    application_file.unlink()
    _write_file(
        project_root / "src/enclosure/features/orders/report/unexpected.py",
        "VALUE = 1\n",
    )

    result = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert result.returncode == 1
    assert "Drifts:" in result.stdout
    assert "- orders/report (compact)" in result.stdout
    assert "missing:" in result.stdout
    assert "  - application.py" in result.stdout
    assert "extra:" in result.stdout
    assert "  - unexpected.py" in result.stdout


def test_recipe_drifts_ignore_configured_skip_files(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {"orders/report": "compact"})
    _write_file(
        project_root / "src/enclosure/features/orders/report/__pycache__/ignored.py",
        "VALUE = 1\n",
    )
    _write_file(
        project_root / ".enclosure/.cache/generated.py",
        "VALUE = 1\n",
    )

    result = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert result.returncode == 0, result.stderr
    assert "No recipe drifts found." in result.stdout
    assert "ignored.py" not in result.stdout
    assert ".cache" not in result.stdout


def test_recipe_drifts_ignore_unmapped_actual_modules(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {"orders/report": "compact"})
    _write_file(
        project_root / "src/enclosure/features/billing/report/application.py",
        "def run():\n    return 2\n",
    )

    result = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert result.returncode == 0, result.stderr
    assert "No recipe drifts found." in result.stdout
    assert "billing/report" not in result.stdout


def test_recipe_drifts_allow_slot_growth_but_report_forbidden_slot_shapes(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {"billing/report": "layered"})
    _write_layered_recipe_set(project_root)
    _write_layered_module(project_root, "billing/report")
    _write_file(
        project_root / "src/enclosure/features/billing/report/application/helpers.py",
        "def helper():\n    return 1\n",
    )
    _write_file(
        project_root / "src/enclosure/features/billing/report/application.py",
        "def legacy():\n    return 1\n",
    )

    result = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert result.returncode == 1
    assert "- billing/report (layered)" in result.stdout
    assert "extra:" in result.stdout
    assert "  - application.py" in result.stdout
    assert "application/helpers.py" not in result.stdout


def test_recipe_drifts_report_composed_role_missing_fragment_file(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {"orders/report": "compact+domain-file"})
    _write_domain_file_fragment(project_root)

    result = run_cli(project_root, "workspace", "recipe", "--drifts")

    assert result.returncode == 1
    assert "- orders/report: compact+domain-file (composed/compact+domain-file)" in result.stdout
    assert "- orders/report (compact+domain-file)" in result.stdout
    assert "missing:" in result.stdout
    assert "  - domain.py" in result.stdout


def test_recipe_drifts_ignore_package_slot_growth_but_bench_reports_it(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(
        project_root,
        {"orders/report": "compact", "billing/report": "layered"},
    )
    _write_layered_recipe_set(project_root)
    _write_layered_module(project_root, "billing/report")
    _write_file(
        project_root / "src/enclosure/features/billing/report/domain/service.py",
        "VALUE = 1\n",
    )

    drifts = run_cli(project_root, "workspace", "recipe", "--drifts")
    bench = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "billing/report",
        "--html",
        ".enclosure/package-growth.html",
    )

    assert drifts.returncode == 0, drifts.stderr
    assert "No recipe drifts found." in drifts.stdout
    assert "domain/service.py" not in drifts.stdout
    assert bench.returncode == 1
    assert "Forbidden residue: 0" in bench.stdout
    assert "Slot growth: 1" in bench.stdout
    assert "Classification: local" in bench.stdout


def test_recipe_bench_requires_html_path_for_module_preview(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    result = run_cli(project_root, "workspace", "recipe", "--bench", "orders/report")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "--html is required with --bench" in result.stderr


def test_recipe_bench_reports_unmapped_modules_and_writes_html(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "billing/report",
        "--html",
        ".enclosure/unmapped.html",
    )

    assert result.returncode == 1
    assert "Bench preview for module 'billing/report'." in result.stdout
    assert "Role: unknown" in result.stdout
    assert "Classification: unstable" in result.stdout
    assert "module_unmapped" in result.stdout
    assert (project_root / ".enclosure/unmapped.html").is_file()


def test_recipe_bench_reports_repeated_slot_growth_as_established(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(
        project_root,
        {
            "orders/report": "layered",
            "billing/report": "layered",
            "inventory/report": "layered",
        },
    )
    _write_layered_recipe_set(project_root)
    for module_name in ("orders/report", "billing/report", "inventory/report"):
        _write_layered_module(project_root, module_name)
        _write_file(
            project_root
            / "src/enclosure/features"
            / module_name
            / "application/helpers.py",
            "def helper():\n    return 1\n",
        )

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "orders/report",
        "--html",
        ".enclosure/bench.html",
    )

    assert result.returncode == 1
    assert "Same-role modules: 3" in result.stdout
    assert "Local warp: 1" in result.stdout
    assert "Slot growth: 1" in result.stdout
    assert "Repeated warp: 1" in result.stdout
    assert "Classification: established" in result.stdout


def test_recipe_bench_reports_disjoint_same_role_warp_as_unstable(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(
        project_root,
        {"orders/report": "layered", "billing/report": "layered"},
    )
    _write_layered_recipe_set(project_root)
    _write_layered_module(project_root, "orders/report")
    _write_layered_module(project_root, "billing/report")
    _write_file(
        project_root / "src/enclosure/features/orders/report/application/alpha.py",
        "ALPHA = 1\n",
    )
    _write_file(
        project_root / "src/enclosure/features/billing/report/domain/extra.py",
        "EXTRA = 1\n",
    )

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "orders/report",
        "--html",
        ".enclosure/unstable.html",
    )

    assert result.returncode == 1
    assert "Same-role modules: 2" in result.stdout
    assert "Local warp: 1" in result.stdout
    assert "Classification: unstable" in result.stdout


def test_recipe_bench_reports_content_weight_and_binary_file_content(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _write_file(
        project_root / "src/enclosure/features/orders/report/application.py",
        "\n".join(f"VALUE_{index} = {index}" for index in range(301)) + "\n",
    )
    binary_file = project_root / "src/enclosure/features/orders/report/blob.bin"
    binary_file.write_bytes(b"\xff\xfe\x00")

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "orders/report",
        "--html",
        ".enclosure/content.html",
    )
    html = (project_root / ".enclosure/content.html").read_text(encoding="utf-8")

    assert result.returncode == 1
    assert "Content weight: 1" in result.stdout
    assert "Forbidden residue: 1" in result.stdout
    assert "Classification: local" in result.stdout
    assert "application.py" in html
    assert "301 lines" in html
    assert "[binary or non-UTF-8 file]" in html


def test_recipe_bench_all_aggregates_violations_without_hiding_clean_modules(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(
        project_root,
        {"orders/report": "compact", "missing/report": "compact"},
    )

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench-all",
        "--html",
        ".enclosure/index.html",
    )

    assert result.returncode == 1
    assert "Workspace warp index." in result.stdout
    assert "Mapped modules: 2" in result.stdout
    assert "Recipe roles: 1" in result.stdout
    assert "mapped_module_missing" in result.stdout
    assert "missing/report" in result.stdout
    assert (project_root / ".enclosure/index.html").is_file()


def test_recipe_bench_all_marks_missing_role_recipes_as_blocking(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(
        project_root,
        {"orders/report": "compact", "billing/report": "no-such-recipe"},
    )

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench-all",
        "--html",
        ".enclosure/index.html",
    )
    html = (project_root / ".enclosure/index.html").read_text(encoding="utf-8")

    assert result.returncode == 1
    assert "Workspace warp index." in result.stdout
    assert "Recipe roles: 1" in result.stdout
    assert "Classification: unstable" in result.stdout
    assert "missing_role_recipe" in result.stdout
    assert "<h3>no-such-recipe</h3>" not in html


def test_recipe_bench_marks_global_role_map_failures_as_unstable(
    tmp_path: Path,
) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(
        project_root,
        {"orders/report": "compact", "billing/report": "no-such-recipe"},
    )

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench",
        "orders/report",
        "--html",
        ".enclosure/orders.html",
    )

    assert result.returncode == 1
    assert "Bench preview for module 'orders/report'." in result.stdout
    assert "Local warp: 0" in result.stdout
    assert "Classification: unstable" in result.stdout
    assert "missing_role_recipe" in result.stdout


def test_recipe_bench_all_validates_empty_roles_map(tmp_path: Path) -> None:
    project_root = copy_fixture(tmp_path, "recipe_workspace")
    _configure_recipe_workspace(project_root, {})

    result = run_cli(
        project_root,
        "workspace",
        "recipe",
        "--bench-all",
        "--html",
        ".enclosure/index.html",
    )

    assert result.returncode == 1
    assert "Mapped modules: 0" in result.stdout
    assert "Recipe roles: 0" in result.stdout
    assert "Classification: unstable" in result.stdout
    assert "missing_roles_map" in result.stdout


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")


def _configure_recipe_workspace(project_root: Path, roles_map: dict[str, str]) -> None:
    role_lines = (
        "\n".join(
            f"      {module_name}: {role_name}"
            for module_name, role_name in sorted(roles_map.items())
        )
        if roles_map
        else "      {}"
    )
    _write_file(
        project_root / ".enclosure/enclosure.yaml",
        dedent(
            """
            architecture:
              language: python
              root: src/enclosure/features
              exclusions: [__init__.py]
              boundaries:
                tags:
                  - { name: _t_module, match: "*/*", except: ["*/__init__"], exclude: [] }
                  - { name: _t_application, match: "*/*/application", except: [], exclude: [] }
                  - { name: _t_domain, match: "*/*/domain", except: [], exclude: [] }
                  - { name: _t_infrastructure, match: "*/*/infrastructure", except: [], exclude: [] }
                rules: []
                flow:
                  layers: [application, infrastructure, domain]
                  realms:
                    - { name: _r_module, module_tag: _t_module }
              map:
                top: -1
            workspace:
              recipe:
                skip:
                  - "**/__pycache__/**"
                  - "__pycache__/**"
                  - ".enclosure/.cache/**"
                roles_map:
            """
        )
        + role_lines
        + "\n",
    )


def _write_named_recipe(project_root: Path) -> None:
    module_recipe = project_root / ".enclosure/recipes/module/recipe.yaml"
    module_recipe.write_text(
        module_recipe.read_text(encoding="utf-8").replace(
            "archetypes:\n  - compact\n",
            "archetypes:\n  - compact\n  - named\n",
        ),
        encoding="utf-8",
    )
    _write_file(
        project_root / ".enclosure/recipes/named/recipe.yaml",
        """
        schema_version: 1
        role: archetype
        description: Named fixture module.
        ladder:
          family: module
          rung: named
          slots:
            application: file
        inputs:
          entity:
            type: slug
            required: true
        files:
          - source: templates/application.py.tmpl
            target: "{{ target.path }}/application.py"
        """,
    )
    _write_file(
        project_root / ".enclosure/recipes/named/templates/application.py.tmpl",
        """
        def {{ entity.snake }}_name():
            return "{{ entity.kebab }}"
        """,
    )


def _write_skip_aware_recipe(project_root: Path) -> None:
    _write_file(
        project_root / ".enclosure/recipes/module/recipe.yaml",
        """
        schema_version: 1
        role: container
        description: Fixture recipe container.
        archetypes:
          - skip-aware
        """,
    )
    _write_file(
        project_root / ".enclosure/recipes/skip-aware/recipe.yaml",
        """
        schema_version: 1
        role: archetype
        description: Skip-aware fixture module.
        ladder:
          family: module
          rung: skip-aware
          slots:
            application: file
            domain: file
        files:
          - source: templates/application.py.tmpl
            target: "{{ target.path }}/application.py"
          - source: templates/domain.py.tmpl
            target: "{{ target.path }}/domain.py"
          - source: templates/ignored.py.tmpl
            target: "{{ target.path }}/__pycache__/ignored.py"
        """,
    )
    _write_file(
        project_root / ".enclosure/recipes/skip-aware/templates/application.py.tmpl",
        "def run():\n    return 1\n",
    )
    _write_file(
        project_root / ".enclosure/recipes/skip-aware/templates/domain.py.tmpl",
        "VALUE = 1\n",
    )
    _write_file(
        project_root / ".enclosure/recipes/skip-aware/templates/ignored.py.tmpl",
        "IGNORED = 1\n",
    )


def _write_domain_file_fragment(project_root: Path) -> None:
    _write_file(
        project_root / ".enclosure/recipes/domain-file/recipe.yaml",
        """
        schema_version: 1
        role: fragment
        description: Domain file fragment.
        ladder:
          family: module-slot
          rung: domain-file
          slots:
            domain: file
        files:
          - source: templates/domain.py.tmpl
            target: "{{ target.path }}/domain.py"
        """,
    )
    _write_file(
        project_root / ".enclosure/recipes/domain-file/templates/domain.py.tmpl",
        "VALUE = 1\n",
    )


def _write_layered_recipe_set(project_root: Path) -> None:
    _write_file(
        project_root / ".enclosure/recipes/module/recipe.yaml",
        """
        schema_version: 1
        role: container
        description: Fixture recipe container.
        archetypes:
          - compact
          - layered
        """,
    )
    _write_file(
        project_root / ".enclosure/recipes/domain-fragment/recipe.yaml",
        """
        schema_version: 1
        role: fragment
        description: Domain package fragment.
        ladder:
          family: module-slot
          rung: domain-package
          slots:
            domain: package
        files:
          - source: templates/domain/__init__.py.tmpl
            target: "{{ target.path }}/domain/__init__.py"
        """,
    )
    _write_file(
        project_root
        / ".enclosure/recipes/domain-fragment/templates/domain/__init__.py.tmpl",
        "VALUE = 1\n",
    )
    _write_file(
        project_root / ".enclosure/recipes/layered/recipe.yaml",
        """
        schema_version: 1
        role: archetype
        description: Layered fixture module.
        includes:
          - domain-fragment
        ladder:
          family: module
          rung: layered
          slots:
            application:
              state: split-files
              files:
                - commands.py
                - queries.py
            domain: package
            infrastructure: file
            ui: absent
        files:
          - source: templates/__init__.py.tmpl
            target: "{{ target.path }}/__init__.py"
          - source: templates/application/commands.py.tmpl
            target: "{{ target.path }}/application/commands.py"
          - source: templates/application/queries.py.tmpl
            target: "{{ target.path }}/application/queries.py"
          - source: templates/infrastructure.py.tmpl
            target: "{{ target.path }}/infrastructure.py"
        """,
    )
    _write_file(
        project_root / ".enclosure/recipes/layered/templates/__init__.py.tmpl",
        "",
    )
    _write_file(
        project_root / ".enclosure/recipes/layered/templates/application/commands.py.tmpl",
        "def command():\n    return 1\n",
    )
    _write_file(
        project_root / ".enclosure/recipes/layered/templates/application/queries.py.tmpl",
        "def query():\n    return 1\n",
    )
    _write_file(
        project_root / ".enclosure/recipes/layered/templates/infrastructure.py.tmpl",
        "VALUE = 1\n",
    )


def _write_layered_module(project_root: Path, module_name: str) -> None:
    module_root = project_root / "src/enclosure/features" / module_name
    if module_root.exists():
        shutil.rmtree(module_root)
    _write_file(module_root / "__init__.py", "")
    _write_file(module_root / "application/commands.py", "def command():\n    return 1\n")
    _write_file(module_root / "application/queries.py", "def query():\n    return 1\n")
    _write_file(module_root / "domain/__init__.py", "VALUE = 1\n")
    _write_file(module_root / "infrastructure.py", "VALUE = 1\n")
