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
    source_kind: Annotated[
        str,
        typer.Option(
            "--language",
            help="Set the source extractor when source detection is ambiguous.",
        ),
    ] = "",
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        return
    if docs:
        ui.render_docs("docs.tmpl")
        return

    result = application.bootstrap_project(source_kind=source_kind)
    ui.render(
        result,
        template_name="bootstrap_result.tmpl",
        context={"project_root": result["project_root"]},
    )


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
    ui.render(
        result,
        template_name="update_result.tmpl",
        context={"project_root": result["project_root"]},
    )


@app.command(
    "migrate",
    help="Safely modernize the local enclosure contract.",
)
@ui.command_error_boundary
def migrate_command(
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

    result = application.migrate_project()
    ui.render(
        result,
        template_name="migrate_result.tmpl",
        context={"project_root": result["project_root"]},
    )


ui.set_command_defaults(sync_command, {"llm": False, "docs": False})
ui.set_command_defaults(init_command, {"llm": False, "docs": False, "source_kind": ""})
ui.set_command_defaults(update_command, {"llm": False, "docs": False})
ui.set_command_defaults(migrate_command, {"llm": False, "docs": False})


__all__ = ["app"]
