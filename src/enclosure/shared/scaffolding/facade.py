from __future__ import annotations

from pathlib import Path

from . import manifest as _manifest
from . import render as _render
from . import write as _write
from .composition import compose_scaffolds
from .context import parse_variables as _parse_variables
from .scaffold import RenderedScaffoldFile, Scaffold


class ScaffoldFacade:
    def load_all(self, scaffold_root: Path) -> tuple[Scaffold, ...]:
        return _manifest.find_all(scaffold_root)

    def load(self, scaffold_root: Path, name: str) -> Scaffold:
        return _manifest.get_by_name(scaffold_root, name)

    def parse_variables(self, values: tuple[str, ...]) -> dict[str, str]:
        return _parse_variables(values)

    def compose(
        self,
        scaffold: Scaffold,
        scaffolds: tuple[Scaffold, ...],
    ) -> tuple[Scaffold, ...]:
        return compose_scaffolds(scaffold, scaffolds)

    def render(
        self,
        scaffold: Scaffold,
        scaffolds: tuple[Scaffold, ...],
        target_root: Path,
        target_path: Path | str,
        variables: dict[str, str],
    ) -> tuple[RenderedScaffoldFile, ...]:
        return _render.render(scaffold, scaffolds, target_root, target_path, variables)

    def write(
        self,
        rendered_files: tuple[RenderedScaffoldFile, ...],
        create_paths: tuple[Path, ...],
    ) -> None:
        _write.write(rendered_files, create_paths)
