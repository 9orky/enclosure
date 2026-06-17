from __future__ import annotations

from pathlib import Path

from enclosure.shared import layout

from ..domain import manifest
from . import manifests


class FilePatternRepository:
    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def find_all(
        self,
    ) -> tuple[manifest.Pattern, ...]:
        if not self.root_path.is_dir():
            return ()

        return tuple(
            self._load_pattern(pattern_root, layout.recipe_manifest_path(pattern_root))
            for pattern_root in sorted(
                self._iter_pattern_roots(),
                key=lambda path: path.name,
            )
        )

    def get_by_name(
        self,
        name: str,
    ) -> manifest.Pattern:
        pattern_root = self.root_path / name
        manifest_path = layout.recipe_manifest_path(pattern_root)
        if not manifest_path.is_file():
            raise LookupError(name)

        return self._load_pattern(pattern_root, manifest_path)

    def _iter_pattern_roots(self):
        for child in self.root_path.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir() and layout.recipe_manifest_path(child).is_file():
                yield child

    def _load_pattern(
        self,
        pattern_root: Path,
        manifest_path: Path,
    ) -> manifest.Pattern:
        return manifests.load_pattern_manifest(
            pattern_root,
            manifest_path,
        )


__all__ = ["FilePatternRepository"]
