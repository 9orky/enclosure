from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Create or refresh the project-local enclosure contract.",
    invoke_without_command=True,
    no_args_is_help=True,
)


@app.callback()
@ui.command_error_boundary
def sync_command(
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
        raise typer.Exit()
    if docs:
        ui.render_docs("docs.tmpl")
        raise typer.Exit()


@app.command(
    "init",
    help="Create the project-local enclosure contract in the target repository.",
)
@ui.command_error_boundary
def init_command(
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

    result = application.bootstrap_project()
    ui.render(result, template_name="bootstrap_result.tmpl", context={})


@app.command(
    "update",
    help="Refresh packaged shared assets in an existing enclosure contract.",
)
@ui.command_error_boundary
def update_command(
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

    result = application.update_project()
    ui.render(result, template_name="update_result.tmpl", context={})


ui.set_command_defaults(sync_command, {"llm": False, "docs": False})
ui.set_command_defaults(init_command, {"llm": False, "docs": False})
ui.set_command_defaults(update_command, {"llm": False, "docs": False})


__all__ = ["app"]
