from __future__ import annotations

import select
import sys
import time
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
        if value is None:
            raise ValueError("Plan title is required: workspace plan start TITLE")
        plan = module.start(value)
        ui.render(
            plan,
            template_name="started.tmpl",
            context={"project_root": module.status().project_root},
        )
        return
    if action == "live":
        _run_live(module, value or "Live Plan Session")
        return
    if action == "connect":
        _connect(module, value == "once")
        return
    if action == "ask":
        question = value or _read_stdin_text()
        explanation = detail or "Agent raised this live-session question."
        asked = module.ask_question(question, explanation)
        typer.echo("Question submitted.")
        typer.echo(f"Id: {asked.id}")
        typer.echo(f"Status: {asked.status.value}")
        return
    if action == "answer":
        if value is None:
            raise ValueError("Question id is required: workspace plan answer QUESTION_ID")
        answer = detail or _read_stdin_text()
        answered = module.answer_question(value, answer)
        typer.echo("Answer recorded.")
        typer.echo(f"Id: {answered.id}")
        typer.echo(f"Status: {answered.status.value}")
        return
    if action == "next":
        plan = module.next()
        typer.echo(f"Advanced plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "agent":
        context = module.agent()
        typer.echo(f"Agent context for stage: {context.stage_id}")
        typer.echo("Files:")
        for file_model in context.file_models:
            source = " native-schema" if file_model.native_schema_source else ""
            typer.echo(f"- {file_model.path} [{file_model.model_kind}{source}]")
        return
    if action == "roll":
        plan = module.roll()
        typer.echo(f"Rolled plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Version: {plan.version}")
        return
    if action == "close":
        plan = module.close(value or "Closed by user request.")
        typer.echo(f"Closed plan {plan.id}.")
        typer.echo(f"Stage: {plan.current_stage}")
        typer.echo(f"State: {plan.state.value}")
        typer.echo(f"Active: {'yes' if plan.active else 'no'}")
        typer.echo(f"Version: {plan.version}")
        return
    raise ValueError(f"Unknown plan action: {action}")


def _run_live(module: workspace.WorkspacePlanModule, title: str) -> None:
    plan = module.start_or_resume_live(title)
    typer.echo("Plan live session.")
    typer.echo(f"Plan: {plan.title}")
    typer.echo("Commands: Enter advances, r refreshes, q quits.")
    seen = ""
    while True:
        report = module.live_report()
        signature = _live_signature(report)
        if signature != seen:
            _print_live_report(report)
            seen = signature
        if report.blocking_questions:
            for question in report.blocking_questions:
                typer.echo("")
                typer.echo(f"Question: {question.text}")
                typer.echo(f"Context: {question.explanation}")
                answer = typer.prompt("Answer", default="", show_default=False)
                if answer.strip():
                    module.answer_question(question.id, answer)
                    typer.echo(f"Recorded answer for {question.id}.")
            seen = ""
            continue
        command = _read_live_command()
        if command is None:
            continue
        if command == "q":
            typer.echo("Live session stopped.")
            return
        if command == "r":
            seen = ""
            continue
        if command == "":
            try:
                advanced = module.next()
            except Exception as exc:
                typer.echo(f"Blocked: {exc}")
                seen = ""
                continue
            typer.echo(f"Advanced to {advanced.current_stage}.")
            seen = ""


def _connect(module: workspace.WorkspacePlanModule, once: bool) -> None:
    heartbeat = module.connect_agent()
    typer.echo(f"Agent heartbeat: {heartbeat}")
    if once:
        return
    typer.echo("Connected. Press Ctrl-C to disconnect.")
    try:
        while True:
            module.connect_agent()
            time.sleep(2)
    except KeyboardInterrupt:
        typer.echo("Disconnected.")


def _print_live_report(report: workspace.LivePlanReport) -> None:
    _clear_live_screen()
    typer.echo("")
    typer.echo(f"Stage: {report.current_stage}")
    typer.echo(f"State: {report.state}")
    typer.echo(f"Agent: {'connected' if report.agent_connected else 'waiting'}")
    typer.echo(f"Questions: {len(report.questions)}")
    if report.review_files:
        typer.echo("Review files:")
        for path in report.review_files:
            typer.echo(f"- {report.plan_root / path}")
    if report.blocking_questions:
        typer.echo("Blocking questions:")
        for question in report.blocking_questions:
            typer.echo(f"- {question.id}: {question.text}")
    else:
        typer.echo("No blocking questions. Enter advances, r refreshes, q quits.")


def _live_signature(report: workspace.LivePlanReport) -> str:
    question_ids = ",".join(
        f"{question.id}:{question.status.value}:{question.blocking}"
        for question in report.questions
    )
    return "|".join(
        [
            report.current_stage,
            report.state,
            str(report.agent_connected),
            question_ids,
        ]
    )


def _read_live_command() -> str | None:
    if not sys.stdin.isatty():
        time.sleep(0.5)
        return None
    readable, _, _ = select.select([sys.stdin], [], [], 0.5)
    if not readable:
        return None
    return sys.stdin.readline().strip()


def _clear_live_screen() -> None:
    if sys.stdout.isatty():
        typer.echo("\033[2J\033[H", nl=False)


def _read_stdin_text() -> str:
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read().strip()


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
