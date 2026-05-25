from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Validate file and symbol shape limits from the architecture agreement.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def shape_command(
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

    report = application.build_shape_report()
    ui.render(report, template_name="report.tmpl", context={})

    ui.exit_if_findings(report.violations)


ui.set_command_defaults(shape_command, {"llm": False, "docs": False})


__all__ = ["app"]
