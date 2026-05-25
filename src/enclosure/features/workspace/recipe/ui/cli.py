from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from enclosure.shared import layout, ui

from .. import application

app = typer.Typer(
    help="Render a manifest recipe into the current project contract.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def recipe_command(
    recipe_name: Annotated[str | None, typer.Argument()],
    path: Annotated[str | None, typer.Argument()],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview what the recipe would create without writing files.",
        ),
    ],
    raw_variables: Annotated[
        list[str] | None,
        typer.Option(
            "--var",
            help="Pass a recipe variable as key=value. Can be used more than once.",
        ),
    ],
    list_requested: Annotated[
        bool,
        typer.Option("--list", help="List available recipes."),
    ],
    show_requested: Annotated[
        bool,
        typer.Option("--show", help="Show recipe inputs and target files."),
    ],
    check_requested: Annotated[
        bool,
        typer.Option(
            "--check",
            help=(
                "Validate recipe manifests and template rendering without writing "
                "generated files."
            ),
        ),
    ],
    llm: Annotated[
        bool,
        typer.Option("--llm", help="Print LLM-focused guidance for this command."),
    ],
    docs: Annotated[
        bool,
        typer.Option(
            "--docs",
            help="Print human-focused documentation for this command.",
        ),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        return
    if docs:
        ui.render_docs("docs.tmpl")
        return

    project_root = layout.current_project_root()
    recipe_root = layout.current_recipes_root()
    recipe_root_label = ui.present_path(recipe_root, project_root)
    variables = application.parse_variables(tuple(raw_variables or ()))

    if list_requested:
        ui.render(
            None,
            template_name="recipe_list.tmpl",
            context={"recipes": application.list_recipes(recipe_root=recipe_root)},
        )
        return

    if check_requested:
        report = application.check_recipes(
            recipe_root=recipe_root,
            recipe_name=recipe_name,
            target_path=Path(path) if path is not None else None,
            variables=variables,
        )
        ui.render(report, template_name="check_report.tmpl", context={})
        if not report.passed():
            ui.exit_with_error()
        return

    if not recipe_name:
        raise ValueError("Recipe name is required unless --list is used")

    if show_requested:
        recipe = application.show_recipe(
            recipe_name,
            recipe_root=recipe_root,
        )
        ui.render(
            None,
            template_name="recipe_summary.tmpl",
            context={
                "recipe": recipe,
                "recipe_name": recipe_name,
                "recipe_root_label": recipe_root_label,
            },
        )
        if recipe is None:
            ui.exit_with_error()
        return

    if path is None:
        raise ValueError("Target path is required")

    target_path = Path(path)

    if dry_run:
        result = application.describe_recipe_generation(
            recipe_name,
            target_path,
            recipe_root=recipe_root,
            variables=variables,
        )
        ui.render(
            None,
            template_name="dry_run_result.tmpl",
            context={
                "result": result,
                "recipe_root_label": recipe_root_label,
            },
        )
        if not result["recipe_found"]:
            ui.exit_with_error()
        return

    result = application.generate_recipe(
        recipe_name,
        target_path,
        recipe_root=recipe_root,
        variables=variables,
    )
    ui.render(
        None,
        template_name="generate_result.tmpl",
        context={
            "result": result,
            "recipe_root_label": recipe_root_label,
        },
    )
    if not result["recipe_found"]:
        ui.exit_with_error()


ui.set_command_defaults(
    recipe_command,
    {
        "recipe_name": None,
        "path": None,
        "dry_run": False,
        "raw_variables": None,
        "list_requested": False,
        "show_requested": False,
        "check_requested": False,
        "llm": False,
        "docs": False,
    },
)


__all__ = ["app"]
