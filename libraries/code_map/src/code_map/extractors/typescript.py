from __future__ import annotations

from dataclasses import dataclass
from posixpath import normpath
from pathlib import PurePosixPath

from ..definitions import SourceImport
from .base import SourceExtractor


@dataclass(frozen=True)
class TypeScriptExtractor(SourceExtractor):
    language = "typescript"
    file_extensions = (".ts", ".tsx", ".js", ".jsx")
    command = "node"
    extractor_file = "typescript_extractor.js"

    def normalize_import(
        self,
        source_id: str,
        source_import: SourceImport,
        known_source_ids: set[str],
    ) -> SourceImport:
        normalized_path = source_import.normalized_path
        if source_import.is_relative:
            normalized_path = normpath(
                PurePosixPath(source_id).parent.joinpath(source_import.path).as_posix()
            )
            normalized_path = self.normalize_source_id(normalized_path)

        return SourceImport(
            path=source_import.path,
            is_relative=source_import.is_relative,
            normalized_path=normalized_path,
            imported_name=source_import.imported_name,
            is_aliased=source_import.is_aliased,
            crossing_type=source_import.crossing_type,
            file_barrier_crossed=(
                source_import.file_barrier_crossed
                and normalized_path in known_source_ids
            ),
            statement_id=source_import.statement_id,
            join_key=normalized_path if source_import.join_key else "",
            uses_joined_import=source_import.uses_joined_import,
        )


__all__ = ["TypeScriptExtractor"]
