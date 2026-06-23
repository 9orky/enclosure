from __future__ import annotations

from pathlib import Path

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
