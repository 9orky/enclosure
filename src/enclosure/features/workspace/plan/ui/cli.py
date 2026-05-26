from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Create user-owned module planning documents in the enclosure workspace.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def plan_command(
    name: Annotated[str | None, typer.Argument()],
    show: Annotated[
        bool,
        typer.Option(
            "--show",
            help="Print the rendered plan scaffold without writing it.",
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite an existing plan document.",
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

    if name is None:
        raise ValueError("Plan name is required")

    if show:
        document = application.describe_plan_document(name)
        ui.render(document, template_name="show.tmpl", context={})
        return

    result = application.create_plan_document(name, force=force)
    ui.render(result, template_name="result.tmpl", context={})
    if result.preserved:
        ui.exit_with_error()


ui.set_command_defaults(
    plan_command,
    {
        "name": None,
        "show": False,
        "force": False,
        "llm": False,
        "docs": False,
    },
)


__all__ = ["app"]
