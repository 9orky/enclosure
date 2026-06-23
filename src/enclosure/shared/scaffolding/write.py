from __future__ import annotations

from pathlib import Path

from .scaffold import RenderedScaffoldFile


def write(
    rendered_files: tuple[RenderedScaffoldFile, ...],
    create_paths: tuple[Path, ...],
) -> None:
    create_path_set = {Path(create_path) for create_path in create_paths}
    for rendered_file in rendered_files:
        if rendered_file.target_path not in create_path_set:
            continue
        rendered_file.target_path.parent.mkdir(parents=True, exist_ok=True)
        rendered_file.target_path.write_text(rendered_file.content, encoding="utf-8")
