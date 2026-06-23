from __future__ import annotations

from pathlib import Path

from .composition import _ScaffoldComposer
from .context import _ScaffoldVariableParser
from .manifest import _ScaffoldManifestRepository
from .render import _ScaffoldRenderer
from .scaffold import RenderedScaffoldFile, Scaffold
from .write import _ScaffoldRenderedFileWriter


class ScaffoldFacade:
    def __init__(self) -> None:
        self._repository = _ScaffoldManifestRepository()
        self._variable_parser = _ScaffoldVariableParser()
        self._composer = _ScaffoldComposer()
        self._renderer = _ScaffoldRenderer()
        self._writer = _ScaffoldRenderedFileWriter()

    def load_all(self, scaffold_root: Path) -> tuple[Scaffold, ...]:
        return self._repository.find_all(scaffold_root)

    def load(self, scaffold_root: Path, name: str) -> Scaffold:
        return self._repository.get_by_name(scaffold_root, name)

    def parse_variables(self, values: tuple[str, ...]) -> dict[str, str]:
        return self._variable_parser.parse(values)

    def compose(
        self,
        scaffold: Scaffold,
        scaffolds: tuple[Scaffold, ...],
    ) -> tuple[Scaffold, ...]:
        return self._composer.compose(scaffold, scaffolds)

    def render(
        self,
        scaffold: Scaffold,
        scaffolds: tuple[Scaffold, ...],
        target_root: Path,
        target_path: Path | str,
        variables: dict[str, str],
    ) -> tuple[RenderedScaffoldFile, ...]:
        return self._renderer.render(scaffold, scaffolds, target_root, target_path, variables)

    def write(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
        create_paths: tuple[Path, ...],
    ) -> None:
        self._writer.write(rendered_files, create_paths)
