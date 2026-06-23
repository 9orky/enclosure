from __future__ import annotations

from typing import Annotated

import typer

from .features.architecture.boundaries import ui as architecture_boundaries_ui
from .features.architecture.clusters import ui as architecture_clusters_ui
from .features.architecture.coherence import ui as architecture_coherence_ui
from .features.architecture.health import ui as architecture_health_ui
from .features.architecture.map import ui as architecture_map_ui
from .features.architecture.pressure import ui as architecture_pressure_ui
from .features.architecture.shape import ui as architecture_shape_ui
from .features.health.report import ui as health_report_ui
from .features.workspace.health import ui as workspace_health_ui
from .features.workspace.plan import ui as workspace_plan_ui
from .features.workspace.recipe import ui as workspace_recipe_ui
from .features.workspace.rules import ui as workspace_rules_ui
from .features.workspace.sync import ui as workspace_sync_ui
from .shared import ui

app = typer.Typer(
    name="enclosure",
    help=(
        "Bootstrap a project-local architecture contract, inspect dependency "
        "rules, and generate shared project scaffolding."
    ),
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
@ui.command_error_boundary
def root_command(
    ctx: typer.Context,
    llm: Annotated[
        bool,
        typer.Option("--llm", help="Print LLM-focused guidance for this CLI."),
    ],
    docs: Annotated[
        bool,
        typer.Option("--docs", help="Print human-focused documentation for this CLI."),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        raise typer.Exit()
    if docs:
        ui.render_docs("docs.tmpl")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        ui.render_splash()
        raise typer.Exit()


def _add_callback_app(parent: typer.Typer, child: typer.Typer, *, name: str) -> None:
    callback = child.registered_callback
    if callback is None or callback.callback is None:
        raise RuntimeError(f"{name} app does not expose a callback command")

    help_text = child.info.help
    if not isinstance(help_text, str):
        help_text = None
    parent.command(name, help=help_text)(callback.callback)


workspace_app = typer.Typer(
    help="Manage the project-local enclosure workspace contract.",
    invoke_without_command=True,
    no_args_is_help=True,
)


@workspace_app.callback()
@ui.command_error_boundary
def workspace_command(
    llm: Annotated[
        bool,
        typer.Option(
            "--llm",
            help="Print LLM-focused guidance for workspace commands.",
        ),
    ],
    docs: Annotated[
        bool,
        typer.Option(
            "--docs",
            help="Print human-focused documentation for workspace commands.",
        ),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        raise typer.Exit()
    if docs:
        ui.render_docs("workspace_docs.tmpl")
        raise typer.Exit()


workspace_app.add_typer(workspace_sync_ui.app, name="sync")
_add_callback_app(workspace_app, workspace_health_ui.app, name="health")
_add_callback_app(workspace_app, workspace_plan_ui.app, name="plan")
_add_callback_app(workspace_app, workspace_recipe_ui.app, name="recipe")
workspace_app.add_typer(workspace_rules_ui.app, name="rules")

architecture_app = typer.Typer(
    help="Inspect a repository's architecture agreement and dependency map.",
    invoke_without_command=True,
    no_args_is_help=True,
)


@architecture_app.callback()
@ui.command_error_boundary
def architecture_command(
    llm: Annotated[
        bool,
        typer.Option(
            "--llm",
            help="Print LLM-focused guidance for architecture commands.",
        ),
    ],
    docs: Annotated[
        bool,
        typer.Option(
            "--docs",
            help="Print human-focused documentation for architecture commands.",
        ),
    ],
) -> None:
    if llm:
        ui.render_llm("llm.tmpl")
        raise typer.Exit()
    if docs:
        ui.render_docs("architecture_docs.tmpl")
        raise typer.Exit()


_add_callback_app(
    architecture_app,
    architecture_boundaries_ui.app,
    name="boundaries",
)
_add_callback_app(
    architecture_app,
    architecture_clusters_ui.app,
    name="clusters",
)
_add_callback_app(
    architecture_app,
    architecture_coherence_ui.app,
    name="coherence",
)
_add_callback_app(
    architecture_app,
    architecture_map_ui.app,
    name="map",
)
_add_callback_app(
    architecture_app,
    architecture_pressure_ui.app,
    name="pressure",
)
_add_callback_app(
    architecture_app,
    architecture_health_ui.app,
    name="health",
)
_add_callback_app(
    architecture_app,
    architecture_shape_ui.app,
    name="shape",
)

app.add_typer(workspace_app, name="workspace")
app.add_typer(architecture_app, name="architecture")
_add_callback_app(app, workspace_plan_ui.app, name="plan")
_add_callback_app(app, health_report_ui.app, name="health")

ui.set_command_defaults(root_command, {"llm": False, "docs": False})
ui.set_command_defaults(workspace_command, {"llm": False, "docs": False})
ui.set_command_defaults(architecture_command, {"llm": False, "docs": False})


def main() -> None:
    app()


__all__ = ["app", "main"]


if __name__ == "__main__":
    main()
