from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Run the catalog Pattern module command.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def catalog_command(
    llm: Annotated[
        bool,
        typer.Option("--llm", help="Print LLM-focused guidance for this command."),
    ],
    docs: Annotated[
        bool,
        typer.Option("--docs", help="Print human-focused documentation for this command."),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        return
    if docs:
        ui.render_docs("docs.tmpl")
        return

    ui.render(
        None,
        template_name="result.tmpl",
        context={"patterns": application.list_current_patterns()},
    )


ui.set_command_defaults(catalog_command, {"llm": False, "docs": False})


__all__ = ["app"]
