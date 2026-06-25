from __future__ import annotations

from typing import Annotated

import typer

from enclosure.shared import ui

from .. import application

app = typer.Typer(
    help="Manage the active event-sourced planning workflow.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def plan_command(
    action: Annotated[str | None, typer.Argument()],
    value: Annotated[str | None, typer.Argument()],
    detail: Annotated[str | None, typer.Argument()],
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

    if action is None:
        report = application.plan_status()
        ui.render(
            report,
            template_name="current.tmpl",
            context={"project_root": report.project_root},
        )
        return
    if action == "start":
        if value is None:
            raise ValueError("Plan title is required: workspace plan start TITLE")
        report = application.plan_status()
        plan = application.start_plan(value)
        ui.render(
            plan,
            template_name="started.tmpl",
            context={"project_root": report.project_root},
        )
        return
    if action == "next":
        plan = application.advance_plan()
        typer.echo(f"Advanced plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "agent":
        context = application.agent_context()
        typer.echo(f"Agent context for stage: {context.stage_id}")
        typer.echo("Files:")
        for file_model in context.file_models:
            source = " native-schema" if file_model.native_schema_source else ""
            typer.echo(f"- {file_model.path} [{file_model.model_kind}{source}]")
        return
    if action == "roll":
        plan = application.roll_plan()
        typer.echo(f"Rolled plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "close":
        plan = application.close_plan(value or "Closed by user request.")
        typer.echo(f"Closed plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Active: {'yes' if plan.active else 'no'}")
        typer.echo(f"Version: {plan.version}")
        return
    raise ValueError(f"Unknown plan action: {action}")


ui.set_command_defaults(
    plan_command,
    {
        "action": None,
        "value": None,
        "detail": None,
        "llm": False,
        "docs": False,
    },
)


__all__ = ["app"]
