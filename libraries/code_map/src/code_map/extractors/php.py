from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..definitions import SourceFile, SourceImport
from .base import (
    SourceExtraction,
    SourceExtractor,
    _collect_extraction_targets,
    _json_from_output,
)


@dataclass(frozen=True)
class PhpExtractor(SourceExtractor):
    language = "php"
    file_extensions = (".php",)
    command = "php"
    extractor_file = "php_extractor.php"

    def extract_files(
        self,
        sources_root: Path,
        exclusions: tuple[str, ...],
    ) -> SourceExtraction:
        script = Path(__file__).parent / "scripts" / self.extractor_file
        assert script.is_file(), f"Extractor script {script} not found"

        targets, files_found, files_excluded = _collect_extraction_targets(
            sources_root,
            self.file_extensions,
            exclusions,
        )
        if not targets:
            return SourceExtraction(
                files={},
                files_found=files_found,
                files_excluded=files_excluded,
            )

        input_data = {
            self.normalize_source_id(target.source_id): str(target.path.resolve())
            for target in targets
        }
        cmd = [self.command, str(script), "--batch", str(sources_root.resolve())]
        raw_files = _json_from_output(cmd, json.dumps(input_data))
        result = {
            source_id: SourceFile.model_validate(source_file)
            for source_id, source_file in raw_files.items()
        }

        known_source_ids = set(result)
        result = {
            source_id: self.normalize_source_file(
                source_id,
                source_file,
                known_source_ids,
            )
            for source_id, source_file in result.items()
        }

        return SourceExtraction(
            files=result,
            files_found=files_found,
            files_excluded=files_excluded,
        )

    def normalize_import(
        self,
        source_id: str,
        source_import: SourceImport,
        known_source_ids: set[str],
    ) -> SourceImport:
        normalized_path = self._known_source_id(
            source_import.normalized_path,
            known_source_ids,
        )
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
            join_key=self._normalized_join_key(normalized_path, source_import),
            uses_joined_import=source_import.uses_joined_import,
        )

    def _normalized_join_key(
        self,
        normalized_path: str,
        source_import: SourceImport,
    ) -> str:
        if not source_import.join_key or not normalized_path:
            return ""
        parts = normalized_path.split("/")
        return "/".join(parts[:-1])

    def _known_source_id(
        self,
        normalized_path: str,
        known_source_ids: set[str],
    ) -> str:
        candidates = (normalized_path, *self._php_source_id_candidates(normalized_path))
        for candidate in candidates:
            if candidate in known_source_ids:
                return candidate
            match = self._unique_suffix_match(candidate, known_source_ids)
            if match is not None:
                return match

        namespace_match = self._namespace_source_id(normalized_path, known_source_ids)
        if namespace_match is not None:
            return namespace_match
        return normalized_path

    def _php_source_id_candidates(self, normalized_path: str) -> tuple[str, ...]:
        parts = [self._source_part(part) for part in normalized_path.split("/") if part]
        return tuple("/".join(parts[index:]) for index in range(len(parts)))

    def _namespace_source_id(
        self,
        normalized_path: str,
        known_source_ids: set[str],
    ) -> str | None:
        namespace_matches: list[str] = []
        for candidate in self._php_source_id_candidates(normalized_path):
            namespace_path = PurePosixPath(candidate).parent.as_posix()
            if not namespace_path or namespace_path == ".":
                continue
            namespace_suffix = f"/{namespace_path}"
            namespace_matches.extend(
                source_id
                for source_id in known_source_ids
                if self._source_parent(source_id) == namespace_path
                or self._source_parent(source_id).endswith(namespace_suffix)
            )

        matches = sorted(set(namespace_matches))
        return matches[0] if len(matches) == 1 else None

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

    def _source_part(self, value: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()

    def _source_parent(self, source_id: str) -> str:
        return PurePosixPath(source_id).parent.as_posix()


__all__ = ["PhpExtractor"]
