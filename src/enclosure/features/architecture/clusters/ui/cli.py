from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Report architecture clusters from the code dependency map.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def clusters_command(
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
            help="Override architecture.clusters.top; -1 shows all, 0 shows none.",
        ),
    ],
    files_top: Annotated[
        int | None,
        typer.Option(
            "--files-top",
            help=(
                "Override architecture.clusters.files_top; "
                "-1 shows all, 0 shows none."
            ),
        ),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        return
    if docs:
        ui.render_docs("docs.tmpl")
        return

    report = application.build_clusters_report_for_limits(top, files_top)
    ui.render(report, template_name="report.tmpl", context={})


ui.set_command_defaults(
    clusters_command,
    {"llm": False, "docs": False, "top": None, "files_top": None},
)


__all__ = ["app"]
