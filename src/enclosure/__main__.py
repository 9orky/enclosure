from __future__ import annotations

from typing import Annotated

import typer

import enclosure.features.architecture.boundaries.ui
import enclosure.features.architecture.clusters.ui
import enclosure.features.architecture.health.ui
import enclosure.features.architecture.map.ui
import enclosure.features.architecture.shape.ui
import enclosure.features.workspace.plan.ui
import enclosure.features.workspace.recipe.ui
import enclosure.features.workspace.rules.ui
import enclosure.features.workspace.sync.ui
from enclosure.shared import ui

app = typer.Typer(
    name="enclosure",
    help=(
        "Bootstrap a project-local architecture contract, inspect dependency "
        "rules, and generate shared project scaffolding."
    ),
    invoke_without_command=True,
    no_args_is_help=True,
)


@app.callback()
@ui.command_error_boundary
def root_command(
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


workspace_app.add_typer(enclosure.features.workspace.sync.ui.app, name="sync")
_add_callback_app(workspace_app, enclosure.features.workspace.plan.ui.app, name="plan")
_add_callback_app(workspace_app, enclosure.features.workspace.recipe.ui.app, name="recipe")
_add_callback_app(workspace_app, enclosure.features.workspace.rules.ui.app, name="rules")

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
    enclosure.features.architecture.boundaries.ui.app,
    name="boundaries",
)
_add_callback_app(
    architecture_app,
    enclosure.features.architecture.clusters.ui.app,
    name="clusters",
)
_add_callback_app(
    architecture_app,
    enclosure.features.architecture.map.ui.app,
    name="map",
)
_add_callback_app(
    architecture_app,
    enclosure.features.architecture.health.ui.app,
    name="health",
)
_add_callback_app(
    architecture_app,
    enclosure.features.architecture.shape.ui.app,
    name="shape",
)

app.add_typer(workspace_app, name="workspace")
app.add_typer(architecture_app, name="architecture")

ui.set_command_defaults(root_command, {"llm": False, "docs": False})
ui.set_command_defaults(workspace_command, {"llm": False, "docs": False})
ui.set_command_defaults(architecture_command, {"llm": False, "docs": False})


def main() -> None:
    app()


__all__ = ["app", "main"]


if __name__ == "__main__":
    main()
