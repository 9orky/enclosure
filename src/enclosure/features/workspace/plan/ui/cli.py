from __future__ import annotations

import sys
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
    if action == "put":
        if value is None:
            raise ValueError("Artifact path is required: workspace plan put PATH")
        content = detail
        if content is None:
            if sys.stdin.isatty():
                raise ValueError(
                    "Artifact content is required as DETAIL or stdin"
                )
            content = sys.stdin.read()
        plan = application.put_stage_artifact(value, content)
        typer.echo(f"Updated artifact {value}.")
        typer.echo(f"Plan: {plan.id}")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "answer":
        if value is None:
            raise ValueError(
                "Question title is required: workspace plan answer TITLE ANSWER"
            )
        answer = detail
        if answer is None:
            if sys.stdin.isatty():
                raise ValueError(
                    "Question answer is required as DETAIL or stdin"
                )
            answer = sys.stdin.read()
        plan = application.answer_stage_question(value, answer)
        typer.echo(f"Answered question: {value}")
        typer.echo(f"Plan: {plan.id}")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "ask":
        if value is None:
            raise ValueError(
                "Question title is required: workspace plan ask TITLE EXPLANATION"
            )
        explanation = detail
        if explanation is None:
            if sys.stdin.isatty():
                raise ValueError(
                    "Question explanation is required as DETAIL or stdin"
                )
            explanation = sys.stdin.read()
        plan = application.ask_stage_question(value, explanation)
        typer.echo(f"Asked question: {value}")
        typer.echo(f"Plan: {plan.id}")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "roll":
        plan = application.roll_plan()
        typer.echo(f"Rolled plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "restore":
        plan = application.restore_plan_projections()
        typer.echo(f"Restored projections for plan {plan.id}.")
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
