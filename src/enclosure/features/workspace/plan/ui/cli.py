from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import workspace

app = typer.Typer(
    help="Manage the active event-sourced planning workflow.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def plan_command(
    action: Annotated[str | None, typer.Argument()],
    title: Annotated[str | None, typer.Argument()],
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

    module = workspace.WorkspacePlanModule.from_current_workspace()
    if action is None:
        report = module.status()
        ui.render(
            report,
            template_name="current.tmpl",
            context={"project_root": report.project_root},
        )
        return
    if action == "start":
        if title is None:
            raise ValueError("Plan title is required: workspace plan start TITLE")
        plan = module.start(title)
        ui.render(
            plan,
            template_name="started.tmpl",
            context={"project_root": module.status().project_root},
        )
        return
    raise ValueError(f"Unknown plan action: {action}")


ui.set_command_defaults(
    plan_command,
    {
        "action": None,
        "title": None,
        "llm": False,
        "docs": False,
    },
)


__all__ = ["app"]
