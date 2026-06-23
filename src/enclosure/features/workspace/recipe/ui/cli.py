from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from enclosure.shared import ui
from enclosure.shared.config import settings

from .. import application

app = typer.Typer(
    help="Render a manifest recipe into the current project contract.",
    invoke_without_command=True,
)


@app.callback()
@ui.command_error_boundary
def recipe_command(
    recipe_name: Annotated[str | None, typer.Argument()],
    path: Annotated[str | None, typer.Argument()],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview what the recipe would create without writing files.",
        ),
    ],
    shell_requested: Annotated[
        bool,
        typer.Option(
            "--shell",
            help="Preview the rendered recipe shell tree and content without writing files.",
        ),
    ],
    tree_requested: Annotated[
        bool,
        typer.Option(
            "--tree",
            help="With --dry-run, show the rendered recipe shell file tree.",
        ),
    ],
    content_requested: Annotated[
        bool,
        typer.Option(
            "--content",
            help="With --dry-run, show rendered file content.",
        ),
    ],
    raw_variables: Annotated[
        list[str] | None,
        typer.Option(
            "--var",
            help="Pass a recipe variable as key=value. Can be used more than once.",
        ),
    ],
    list_requested: Annotated[
        bool,
        typer.Option("--list", help="List available recipes."),
    ],
    show_requested: Annotated[
        bool,
        typer.Option("--show", help="Show recipe inputs and target files."),
    ],
    check_requested: Annotated[
        bool,
        typer.Option(
            "--check",
            help=(
                "Validate recipe manifests and template rendering without writing "
                "generated files."
            ),
        ),
    ],
    drifts_requested: Annotated[
        bool,
        typer.Option(
            "--drifts",
            help="Compare mapped feature modules with their recipe role file trees.",
        ),
    ],
    bench_module: Annotated[
        str | None,
        typer.Option(
            "--bench",
            help="Build an HTML bench preview warp report for a mapped module.",
        ),
    ],
    bench_all_requested: Annotated[
        bool,
        typer.Option(
            "--bench-all",
            help="Build an HTML warp index for every mapped module.",
        ),
    ],
    html_report_path: Annotated[
        Path | None,
        typer.Option(
            "--html",
            help="Write the bench preview HTML report to this path.",
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

    project_root = settings.metadata.project_root
    recipe_root = settings.metadata.recipes_dir
    recipe_root_label = ui.present_path(recipe_root, project_root)
    variables = application.parse_variables(tuple(raw_variables or ()))

    if bench_all_requested:
        if html_report_path is None:
            raise ValueError("--html is required with --bench-all")
        _validate_html_report_path(html_report_path)
        report = application.bench_all_preview(recipe_root=recipe_root)
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        html_report_path.write_text(
            application.render_recipe_bench_all_html(report),
            encoding="utf-8",
        )
        ui.render(
            None,
            template_name="bench_all_result.tmpl",
            context={
                "report": report,
                "html_report_path": html_report_path,
            },
        )
        if not report.passed():
            ui.exit_with_error()
        return

    if bench_module:
        if html_report_path is None:
            raise ValueError("--html is required with --bench")
        _validate_html_report_path(html_report_path)
        report = application.bench_preview(
            bench_module,
            recipe_root=recipe_root,
        )
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        html_report_path.write_text(
            application.render_recipe_bench_html(report),
            encoding="utf-8",
        )
        ui.render(
            None,
            template_name="bench_result.tmpl",
            context={
                "report": report,
                "html_report_path": html_report_path,
            },
        )
        if not report.passed():
            ui.exit_with_error()
        return

    if list_requested:
        ui.render(
            None,
            template_name="recipe_list.tmpl",
            context={"recipes": application.list_recipes(recipe_root=recipe_root)},
        )
        return

    if check_requested:
        report = application.check_recipes(
            recipe_root=recipe_root,
            recipe_name=recipe_name,
            target_path=Path(path) if path is not None else None,
            variables=variables,
        )
        ui.render(report, template_name="check_report.tmpl", context={})
        if not report.passed():
            ui.exit_with_error()
        return

    if drifts_requested:
        report = application.check_recipe_drifts(recipe_root=recipe_root)
        ui.render(report, template_name="drift_report.tmpl", context={})
        if not report.passed():
            ui.exit_with_error()
        return

    if not recipe_name:
        raise ValueError("Recipe name is required unless --list or --drifts is used")

    if show_requested:
        recipe = application.show_recipe(
            recipe_name,
            recipe_root=recipe_root,
        )
        ui.render(
            None,
            template_name="recipe_summary.tmpl",
            context={
                "recipe": recipe,
                "recipe_name": recipe_name,
                "recipe_root_label": recipe_root_label,
            },
        )
        if recipe is None:
            ui.exit_with_error()
        return

    if path is None:
        raise ValueError("Target path is required")

    target_path = Path(path)

    if dry_run or shell_requested:
        result = application.describe_recipe_generation(
            recipe_name,
            target_path,
            recipe_root=recipe_root,
            variables=variables,
        )
        ui.render(
            None,
            template_name="dry_run_result.tmpl",
            context={
                "result": result,
                "recipe_root_label": recipe_root_label,
                "tree_requested": tree_requested or shell_requested,
                "content_requested": content_requested or shell_requested,
            },
        )
        if not result["recipe_found"]:
            ui.exit_with_error()
        return

    result = application.generate_recipe(
        recipe_name,
        target_path,
        recipe_root=recipe_root,
        variables=variables,
    )
    ui.render(
        None,
        template_name="generate_result.tmpl",
        context={
            "result": result,
            "recipe_root_label": recipe_root_label,
        },
    )
    if not result["recipe_found"]:
        ui.exit_with_error()


ui.set_command_defaults(
    recipe_command,
    {
        "recipe_name": None,
        "path": None,
        "dry_run": False,
        "shell_requested": False,
        "tree_requested": False,
        "content_requested": False,
        "raw_variables": None,
        "list_requested": False,
        "show_requested": False,
        "check_requested": False,
        "drifts_requested": False,
        "bench_module": None,
        "bench_all_requested": False,
        "html_report_path": None,
        "llm": False,
        "docs": False,
    },
)


def _validate_html_report_path(html_report_path: Path) -> None:
    if html_report_path.name.startswith("-"):
        raise ValueError("--html must be a file path, not an option flag")


__all__ = ["app"]
