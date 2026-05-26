from __future__ import annotations

from enclosure.__main__ import app


def test_workspace_plan_cli_creates_preserves_overwrites_and_shows_plan(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("enclosure-workspace")
    use_project(project)
    plan_path = project.enclosure_dir / "plans" / "module-design.md"

    show_result = cli_runner.invoke(
        app,
        ["workspace", "plan", "module-design", "--show"],
    )

    assert show_result.exit_code == 0, show_result.output
    assert "Plan target: .enclosure/plans/module-design.md" in show_result.output
    assert "## Public Seam" in show_result.output
    assert not plan_path.exists()

    create_result = cli_runner.invoke(app, ["workspace", "plan", "module-design"])

    assert create_result.exit_code == 0, create_result.output
    assert "Created plan .enclosure/plans/module-design.md" in create_result.output
    assert "## Notes For The Implementing Agent" in plan_path.read_text(
        encoding="utf-8"
    )

    plan_path.write_text("custom draft\n", encoding="utf-8")
    preserve_result = cli_runner.invoke(app, ["workspace", "plan", "module-design"])

    assert preserve_result.exit_code == 1, preserve_result.output
    assert "Preserved existing plan .enclosure/plans/module-design.md" in (
        preserve_result.output
    )
    assert plan_path.read_text(encoding="utf-8") == "custom draft\n"

    overwrite_result = cli_runner.invoke(
        app,
        ["workspace", "plan", "module-design", "--force"],
    )

    assert overwrite_result.exit_code == 0, overwrite_result.output
    assert "Overwrote plan .enclosure/plans/module-design.md" in (
        overwrite_result.output
    )
    assert "custom draft" not in plan_path.read_text(encoding="utf-8")


def test_workspace_plan_cli_requires_initialized_enclosure(
    fixture_project,
    use_project,
    cli_runner,
) -> None:
    project = fixture_project("minimal-python")
    use_project(project)

    result = cli_runner.invoke(app, ["workspace", "plan", "module-design"])

    assert result.exit_code == 1, result.output
    assert "Run `enclosure workspace sync init` first" in result.output
    assert not (project.root / ".enclosure").exists()
