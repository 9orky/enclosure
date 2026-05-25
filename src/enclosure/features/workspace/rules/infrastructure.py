from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import TypeAdapter

from . import domain


class FileRepository(domain.RuleDocumentRepository):
    def __init__(self) -> None:
        self._document_adapter = TypeAdapter(domain.RuleDocumentFile)

    def find(
        self,
        rules_root: Path,
    ) -> tuple[domain.RuleDocumentFile, ...]:
        if not rules_root.is_dir():
            raise FileNotFoundError(f"Workspace rules directory not found: {rules_root}")
        return self._find_in(rules_root)

    def _find_in(self, rules_root) -> tuple[domain.RuleDocumentFile, ...]:
        return tuple(
            self._document_adapter.validate_python(
                {
                    "path": relative_path,
                    "content": child.read_text(encoding="utf-8"),
                }
            )
            for relative_path, child in _iter_visible_files(
                rules_root,
                relative_path=Path(),
                suffix=".md",
            )
        )


file_repository = FileRepository()


def _iter_visible_files(
    directory,
    *,
    relative_path: Path,
    suffix: str | None,
) -> Iterable[tuple[Path, object]]:
    for child in sorted(directory.iterdir(), key=lambda item: item.name):
        if child.name.startswith("."):
            continue

        child_relative_path = relative_path / child.name
        if child.is_dir():
            yield from _iter_visible_files(
                child,
                relative_path=child_relative_path,
                suffix=suffix,
            )
            continue

        if suffix is not None and child_relative_path.suffix != suffix:
            continue

        yield child_relative_path, child


__all__ = ["FileRepository", "file_repository"]
