from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Summarize architecture checks, hotspots, and dependency pressure.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def health_command(
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
    top: Annotated[
        int | None,
        typer.Option(
            "--top",
            help="Override architecture.health.top; -1 shows all, 0 shows none.",
        ),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        return
    if docs:
        ui.render_docs("docs.tmpl")
        return

    report = application.build_health_report_for_top(top)
    ui.render(report, template_name="report.tmpl", context={})
    ui.exit_if_findings(report.blocking_findings)


ui.set_command_defaults(health_command, {"llm": False, "docs": False, "top": None})


__all__ = ["app"]
