from __future__ import annotations

from pathlib import Path

from enclosure.shared import templates

from .composition import compose_scaffolds
from .context import resolve_context
from .errors import ScaffoldError
from .relative_path import _relative_path_value
from .scaffold import RenderedScaffoldFile, Scaffold, _ScaffoldFile


def render(
    scaffold: Scaffold,
    scaffolds: tuple[Scaffold, ...],
    target_root: Path,
    target_path: Path | str,
    variables: dict[str, str],
) -> tuple[RenderedScaffoldFile, ...]:
    resolved_target_root = Path(target_root).resolve()
    target_relative_path = _normalize_target_path(resolved_target_root, target_path)
    composed_scaffolds = compose_scaffolds(scaffold, scaffolds)
    context = resolve_context(composed_scaffolds, target_relative_path, variables)
    rendered_files: list[RenderedScaffoldFile] = []
    for composed_scaffold in composed_scaffolds:
        rendered_files.extend(
            _render_file(
                composed_scaffold,
                scaffold_file,
                resolved_target_root,
                context,
            )
            for scaffold_file in composed_scaffold.files
        )
    return tuple(rendered_files)


def _render_file(
    scaffold: Scaffold,
    scaffold_file: _ScaffoldFile,
    target_root: Path,
    context: dict[str, object],
) -> RenderedScaffoldFile:
    source_path = scaffold_file.source.resolve_from(scaffold.source_root)
    if not source_path.is_file():
        raise ScaffoldError(f"Scaffold template does not exist: {source_path}")

    rendered_target = templates.render_recipe_template(scaffold_file.target, context)
    relative_path = _normalize_rendered_target(rendered_target)
    content = templates.render_recipe_template(
        source_path.read_text(encoding="utf-8"),
        context,
    )
    return RenderedScaffoldFile(
        source_path=source_path,
        target_path=target_root / relative_path,
        relative_path=relative_path,
        content=content,
    )


def _normalize_target_path(target_root: Path, target_path: Path | str) -> Path:
    raw_path = Path(target_path)
    if not raw_path.is_absolute():
        return _relative_path_value(raw_path)
    try:
        return _relative_path_value(raw_path.resolve(strict=False).relative_to(target_root))
    except ValueError as exc:
        raise ScaffoldError("Target path must stay inside the target root") from exc


def _normalize_rendered_target(value: str) -> Path:
    return _relative_path_value(value.strip())
