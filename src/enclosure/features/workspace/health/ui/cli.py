from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui, verbosity

from .. import application

app = typer.Typer(
    help="Summarize workspace contract, rule, and recipe health.",
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
    v: Annotated[
        bool,
        typer.Option("--v", help="Summary health report."),
    ],
    vv: Annotated[
        bool,
        typer.Option("--vv", help="Standard health report."),
    ],
    vvv: Annotated[
        bool,
        typer.Option("--vvv", help="Detailed health report."),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        return
    if docs:
        ui.render_docs("docs.tmpl")
        return

    report = application.build_workspace_health_report()
    report_verbosity = verbosity.report_verbosity_from_flags(v=v, vv=vv, vvv=vvv)
    ui.render(
        report,
        template_name="report.tmpl",
        context={
            "project_root": report.project_root,
            "verbosity": report_verbosity.value,
        },
    )
    ui.exit_if_findings(report.blocking_findings)


ui.set_command_defaults(
    health_command,
    {"llm": False, "docs": False, "v": False, "vv": False, "vvv": False},
)


__all__ = ["app"]
