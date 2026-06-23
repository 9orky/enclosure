from __future__ import annotations

from pathlib import Path

from enclosure.shared import templates

from .composition import _ScaffoldComposer
from .context import _ScaffoldContextFactory
from .errors import ScaffoldError
from .relative_path import _ScaffoldRelativePathNormalizer
from .scaffold import RenderedScaffoldFile, Scaffold, _ScaffoldFile


class _ScaffoldRenderer:
    def __init__(self) -> None:
        self._composer = _ScaffoldComposer()
        self._context_factory = _ScaffoldContextFactory()
        self._paths = _ScaffoldRelativePathNormalizer()

    def render(
        self,
        scaffold: Scaffold,
        scaffolds: tuple[Scaffold, ...],
        target_root: Path,
        target_path: Path | str,
        variables: dict[str, str],
    ) -> tuple[RenderedScaffoldFile, ...]:
        resolved_target_root = Path(target_root).resolve()
        target_relative_path = self._paths.target_path(resolved_target_root, target_path)
        composed_scaffolds = self._composer.compose(scaffold, scaffolds)
        context = self._context_factory.resolve(
            composed_scaffolds,
            target_relative_path,
            variables,
        )
        rendered_files: list[RenderedScaffoldFile] = []
        for composed_scaffold in composed_scaffolds:
            rendered_files.extend(
                self._render_file(
                    composed_scaffold,
                    scaffold_file,
                    resolved_target_root,
                    context,
                )
                for scaffold_file in composed_scaffold.files
            )
        return tuple(rendered_files)

    def _render_file(
        self,
        scaffold: Scaffold,
        scaffold_file: _ScaffoldFile,
        target_root: Path,
        context: dict[str, object],
    ) -> RenderedScaffoldFile:
        source_path = self._source_path(scaffold, scaffold_file)
        relative_path = self._rendered_target(scaffold_file, context)
        content = self._rendered_content(source_path, context)
        return RenderedScaffoldFile(
            source_path=source_path,
            target_path=target_root / relative_path,
            relative_path=relative_path,
            content=content,
        )

    def _source_path(self, scaffold: Scaffold, scaffold_file: _ScaffoldFile) -> Path:
        source_path = scaffold_file.source.resolve_from(scaffold.source_root)
        if not source_path.is_file():
            raise ScaffoldError(f"Scaffold template does not exist: {source_path}")
        return source_path

    def _rendered_target(
        self,
        scaffold_file: _ScaffoldFile,
        context: dict[str, object],
    ) -> Path:
        rendered_target = templates.render_recipe_template(scaffold_file.target, context)
        return self._paths.normalize(rendered_target.strip(), "Scaffold rendered target")

    def _rendered_content(self, source_path: Path, context: dict[str, object]) -> str:
        return templates.render_recipe_template(
            source_path.read_text(encoding="utf-8"),
            context,
        )
