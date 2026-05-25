from __future__ import annotations

from enclosure.__main__ import app


def test_workspace_recipe_cli_lists_shows_checks_dry_runs_and_generates_recipe(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    generated_file = project.root / "generated" / "sample.py"

    list_result = cli_runner.invoke(app, ["workspace", "recipe", "--list"])
    show_result = cli_runner.invoke(
        app,
        ["workspace", "recipe", "component", "--show"],
    )
    check_result = cli_runner.invoke(
        app,
        [
            "workspace",
            "recipe",
            "component",
            "generated",
            "--check",
            "--var",
            "component=sample",
        ],
    )

    assert list_result.exit_code == 0, list_result.output
    assert "component" in list_result.output
    assert show_result.exit_code == 0, show_result.output
    assert "{{ target.path }}/{{ component.snake }}.py" in show_result.output
    assert check_result.exit_code == 0, check_result.output

    dry_run_result = cli_runner.invoke(
        app,
        [
            "workspace",
            "recipe",
            "component",
            "generated",
            "--dry-run",
            "--var",
            "component=sample",
        ],
    )

    assert dry_run_result.exit_code == 0, dry_run_result.output
    assert "generated/sample.py" in dry_run_result.output
    assert not generated_file.exists()

    generate_result = cli_runner.invoke(
        app,
        [
            "workspace",
            "recipe",
            "component",
            "generated",
            "--var",
            "component=sample",
        ],
    )

    assert generate_result.exit_code == 0, generate_result.output
    assert 'class Sample:\n    name = "sample"' in generated_file.read_text(
        encoding="utf-8"
    )


def test_workspace_recipe_check_reports_broken_fixture_recipe(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("broken-enclosure-workspace")
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "recipe", "--check"])

    assert result.exit_code == 1, result.output
    assert "render_failed" in result.output
