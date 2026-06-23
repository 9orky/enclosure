from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui
from enclosure.shared import verbosity as report_verbosity

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

    report = application.build_health_report_for_top(top)
    verbosity = report_verbosity.report_verbosity_from_flags(v=v, vv=vv, vvv=vvv)
    ui.render(
        report,
        template_name="report.tmpl",
        context={
            "project_root": report.project_root,
            "verbosity": verbosity.value,
        },
    )
    ui.exit_if_findings(report.blocking_findings)


ui.set_command_defaults(
    health_command,
    {
        "llm": False,
        "docs": False,
        "top": None,
        "v": False,
        "vv": False,
        "vvv": False,
    },
)


__all__ = ["app"]
