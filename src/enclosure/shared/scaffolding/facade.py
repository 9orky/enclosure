from __future__ import annotations

from pathlib import Path

from . import composition, context, manifest, render, scaffold, write


class ScaffoldFacade:
    def __init__(self) -> None:
        self._repository = manifest._ScaffoldManifestRepository()
        self._variable_parser = context._ScaffoldVariableParser()
        self._composer = composition._ScaffoldComposer()
        self._renderer = render._ScaffoldRenderer()
        self._writer = write._ScaffoldRenderedFileWriter()

    def load_all(self, scaffold_root: Path) -> tuple[scaffold.Scaffold, ...]:
        return self._repository.find_all(scaffold_root)

    def load(self, scaffold_root: Path, name: str) -> scaffold.Scaffold:
        return self._repository.get_by_name(scaffold_root, name)

    def parse_variables(self, values: tuple[str, ...]) -> dict[str, str]:
        return self._variable_parser.parse(values)

    def compose(
        self,
        selected_scaffold: scaffold.Scaffold,
        scaffolds: tuple[scaffold.Scaffold, ...],
    ) -> tuple[scaffold.Scaffold, ...]:
        return self._composer.compose(selected_scaffold, scaffolds)

    def render(
        self,
        selected_scaffold: scaffold.Scaffold,
        scaffolds: tuple[scaffold.Scaffold, ...],
        target_root: Path,
        target_path: Path | str,
        variables: dict[str, str],
    ) -> tuple[scaffold.RenderedScaffoldFile, ...]:
        return self._renderer.render(
            selected_scaffold,
            scaffolds,
            target_root,
            target_path,
            variables,
        )

    def write(
        self,
        rendered_files: tuple[scaffold.RenderedScaffoldFile, ...],
        create_paths: tuple[Path, ...],
    ) -> None:
        self._writer.write(rendered_files, create_paths)
