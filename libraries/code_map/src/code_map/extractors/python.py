from __future__ import annotations

import sys

from dataclasses import dataclass
from posixpath import normpath
from pathlib import PurePosixPath

from ..definitions import SourceImport
from .base import SourceExtractor


@dataclass(frozen=True)
class PythonExtractor(SourceExtractor):
    language = "python"
    file_extensions = (".py",)
    command = sys.executable
    extractor_file = "python_extractor.py"

    def normalize_import(
        self,
        source_id: str,
        source_import: SourceImport,
        known_source_ids: set[str],
    ) -> SourceImport:
        normalized_path = self._normalize_relative_import(source_id, source_import)
        crossing_type = source_import.crossing_type
        if source_import.imported_name and source_import.imported_name != "*":
            module_import_path = "/".join(
                part for part in (normalized_path, source_import.imported_name) if part
            )
            module_source_id = self._known_source_id(module_import_path, known_source_ids)
            if module_source_id in known_source_ids:
                normalized_path = module_source_id
                crossing_type = "module"
            else:
                normalized_path = self._known_source_id(normalized_path, known_source_ids)
        else:
            normalized_path = self._known_source_id(normalized_path, known_source_ids)

        return SourceImport(
            path=source_import.path,
            is_relative=source_import.is_relative,
            normalized_path=normalized_path,
            imported_name=source_import.imported_name,
            is_aliased=source_import.is_aliased,
            crossing_type=crossing_type,
            file_barrier_crossed=(
                source_import.file_barrier_crossed
                and normalized_path in known_source_ids
            ),
            statement_id=source_import.statement_id,
            join_key=self._normalized_join_key(normalized_path, source_import),
            uses_joined_import=source_import.uses_joined_import,
        )

    def _normalize_relative_import(
        self,
        source_id: str,
        source_import: SourceImport,
    ) -> str:
        if not source_import.is_relative:
            return source_import.normalized_path

        level = len(source_import.path) - len(source_import.path.lstrip("."))
        module_path = source_import.path[level:].replace(".", "/").strip("/")
        package_path = PurePosixPath(source_id).parent
        for _ in range(max(level - 1, 0)):
            package_path = package_path.parent

        return normpath(
            "/".join(part for part in (package_path.as_posix(), module_path) if part)
        )

    def _known_source_id(
        self,
        normalized_path: str,
        known_source_ids: set[str],
    ) -> str:
        candidates = (normalized_path, f"{normalized_path}/__init__")
        for candidate in candidates:
            if candidate in known_source_ids:
                return candidate
            match = self._unique_suffix_match(candidate, known_source_ids)
            if match is not None:
                return match
        return normalized_path

    def _normalized_join_key(
        self,
        normalized_path: str,
        source_import: SourceImport,
    ) -> str:
        if not source_import.join_key or not normalized_path:
            return ""
        parent = PurePosixPath(normalized_path).parent.as_posix()
        return "" if parent == "." else parent

    def _unique_suffix_match(
        self,
        candidate: str,
        known_source_ids: set[str],
    ) -> str | None:
        suffix = f"/{candidate}"
        matches = sorted(
            source_id
            for source_id in known_source_ids
            if source_id == candidate or source_id.endswith(suffix)
        )
        return matches[0] if len(matches) == 1 else None


__all__ = ["PythonExtractor"]
