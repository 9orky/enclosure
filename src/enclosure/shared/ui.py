from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from functools import wraps
from importlib import resources
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, get_type_hints

import typer
import modwire.architecture.render
from jinja2 import Environment, StrictUndefined

from enclosure.shared import architecture, layout, limits

P = ParamSpec("P")
R = TypeVar("R")

_TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    lstrip_blocks=True,
    trim_blocks=True,
    undefined=StrictUndefined,
)


def command_error_boundary(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except typer.Exit:
            raise
        except Exception as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(1) from exc

    return wrapped


def render(
    data: object | Mapping[str, Any] | None,
    *,
    template_name: str,
    context: Mapping[str, Any],
) -> None:
    render_context = dict(data) if isinstance(data, Mapping) else {}
    if data is not None:
        render_context.update(
            {
                "data": data,
                "output": data,
                "report": data,
                "result": data,
            }
        )
    render_context.update(dict(context))
    render_context["project_root"] = layout.current_project_root()
    typer.echo(
        _render_text(
            _local_template_text(template_name),
            render_context,
        ).rstrip("\n")
    )


def render_llm(template_name: str) -> None:
    typer.echo(
        _render_text(
            _local_template_text(template_name),
            {
                "project_root": layout.current_project_root(),
                "config_yaml": _packaged_resource_text("enclosure.yaml"),
            },
        ).rstrip("\n")
    )


def render_docs(template_name: str) -> None:
    typer.echo(
        _render_text(
            _local_template_text(template_name),
            {
                "project_root": layout.current_project_root(),
            },
        ).rstrip("\n")
    )


def _local_template_text(template_name: str) -> str:
    frame = inspect.currentframe()
    for _ in range(2):
        if frame is None or frame.f_back is None:
            raise RuntimeError("Could not resolve template caller")
        frame = frame.f_back

    anchor = frame.f_globals.get("__package__") or frame.f_globals.get("__name__")
    if not isinstance(anchor, str) or not anchor:
        raise RuntimeError("Could not resolve template package")

    template_path = resources.files(anchor).joinpath("templates", template_name)
    return template_path.read_text(encoding="utf-8")


def _packaged_resource_text(name: str) -> str:
    resource_path = resources.files("enclosure").joinpath("resources", name)
    return resource_path.read_text(encoding="utf-8").rstrip("\n")


def _render_text(template: str, context: Mapping[str, Any]) -> str:
    return _TEMPLATE_ENVIRONMENT.from_string(template).render(**context)


def _layer_summary(layers: Any) -> str:
    if not layers:
        return ""
    summary = ", ".join(f"{layer.name} {len(layer.files)}" for layer in layers)
    return f" ({summary})"


def _rule_document_status(document: Any) -> str:
    if document.exception:
        return f"parse-error - {document.exception}"
    if not document.violations:
        return "ok"
    details = "; ".join(
        _rule_violation_text(violation)
        for violation in document.violations
    )
    return f"{len(document.violations)} violation(s) - {details}"


def _rule_violation_text(violation: Any) -> str:
    if violation.reference_path:
        return f"{violation.code} ({violation.reference_path}) - {violation.message}"
    if violation.section_heading:
        return f"{violation.code} ({violation.section_heading}) - {violation.message}"
    return f"{violation.code} - {violation.message}"


def _violation_subject(violation: Any) -> str:
    if getattr(violation, "symbol_name", ""):
        return f"{violation.source_id}:{violation.symbol_name}"
    return str(violation.source_id)


def present_path(path: Path, project_root: Path) -> str:
    return _relative_label(path, project_root)


def _relative_label(path: Path | None, root: Path) -> str:
    if path is None:
        return ""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


_TEMPLATE_ENVIRONMENT.filters.update(
    {
        "architecture_violations": modwire.architecture.render.violations,
        "layer_summary": _layer_summary,
        "limit_items": limits.apply_limit,
        "present_path": _relative_label,
        "rule_document_status": _rule_document_status,
        "scan_summary": architecture.scan_summary,
        "violation_subject": _violation_subject,
    }
)


def exit_if_findings(findings: object) -> None:
    if findings:
        exit_with_error()


def set_command_defaults(
    command: Callable[..., Any],
    defaults: Mapping[str, object],
) -> None:
    signature = inspect.signature(command)
    annotations = get_type_hints(command, include_extras=True)
    command.__signature__ = signature.replace(
        parameters=tuple(
            parameter.replace(
                annotation=annotations.get(parameter.name, parameter.annotation),
                default=defaults[parameter.name],
            )
            if parameter.name in defaults
            else parameter
            for parameter in signature.parameters.values()
        )
    )


def exit_with_error() -> None:
    raise typer.Exit(1)


__all__ = [
    "command_error_boundary",
    "exit_if_findings",
    "exit_with_error",
    "present_path",
    "render",
    "render_docs",
    "render_llm",
    "set_command_defaults",
]
