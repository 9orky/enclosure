from __future__ import annotations

from pathlib import Path

from . import scaffold


class _ScaffoldRenderedFileWriter:
    def write(
        self,
        rendered_files: tuple[scaffold.RenderedScaffoldFile, ...],
        create_paths: tuple[Path, ...],
    ) -> None:
        create_path_set = self._create_path_set(create_paths)
        for rendered_file in rendered_files:
            if self._should_write(rendered_file, create_path_set):
                self._write_file(rendered_file)

    def _create_path_set(self, create_paths: tuple[Path, ...]) -> set[Path]:
        return {Path(create_path) for create_path in create_paths}

    def _should_write(
        self,
        rendered_file: scaffold.RenderedScaffoldFile,
        create_paths: set[Path],
    ) -> bool:
        return rendered_file.target_path in create_paths

    def _write_file(self, rendered_file: scaffold.RenderedScaffoldFile) -> None:
        rendered_file.target_path.parent.mkdir(parents=True, exist_ok=True)
        rendered_file.target_path.write_text(rendered_file.content, encoding="utf-8")
