from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from subprocess import run
from typing import Protocol

from ..definitions import SourceFile, SourceImport


@dataclass(frozen=True)
class SourceExtraction:
    files: dict[str, SourceFile]
    files_found: int
    files_excluded: int


@dataclass(frozen=True)
class ExtractionTarget:
    source_id: str
    path: Path


class SourceExtractor(Protocol):
    language: str
    file_extensions: tuple[str, ...]
    command: str
    extractor_file: str

    def normalize_source_id(self, value: str) -> str:
        source_id = value.strip().strip("/")
        for file_extension in self.file_extensions:
            if source_id.endswith(file_extension):
                return source_id[: -len(file_extension)]
        return source_id

    def normalize_import(
        self,
        source_id: str,
        source_import: SourceImport,
        known_source_ids: set[str],
    ) -> SourceImport:
        if source_import.normalized_path in known_source_ids:
            return source_import
        return SourceImport(
            path=source_import.path,
            is_relative=source_import.is_relative,
            normalized_path=source_import.normalized_path.strip().strip("/"),
            imported_name=source_import.imported_name,
            is_aliased=source_import.is_aliased,
            crossing_type=source_import.crossing_type,
            file_barrier_crossed=False,
            statement_id=source_import.statement_id,
            join_key=source_import.join_key,
            uses_joined_import=source_import.uses_joined_import,
        )

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
        result = {}
        for target in targets:
            cmd = [
                self.command,
                str(script),
                str(target.path.resolve()),
                str(sources_root.resolve()),
            ]
            result[self.normalize_source_id(target.source_id)] = (
                SourceFile.model_validate(_json_from_output(cmd))
            )

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

    def normalize_source_file(
        self,
        source_id: str,
        source_file: SourceFile,
        known_source_ids: set[str],
    ) -> SourceFile:
        return SourceFile(
            imports=[
                self.normalize_import(source_id, source_import, known_source_ids)
                for source_import in source_file.imports
            ],
            classes=source_file.classes,
            interfaces=source_file.interfaces,
            types=source_file.types,
            abstract_classes=source_file.abstract_classes,
            functions=source_file.functions,
            line_count=source_file.line_count,
            code_line_count=source_file.code_line_count,
            public_symbol_count=source_file.public_symbol_count,
        )


def _collect_extraction_targets(
    sources_root: Path,
    file_extensions: tuple[str, ...],
    exclusions: tuple[str, ...],
) -> tuple[tuple[ExtractionTarget, ...], int, int]:
    targets = []
    files_found = 0
    files_excluded = 0
    for path in sorted(sources_root.rglob("*")):
        if path.suffix not in file_extensions:
            continue

        files_found += 1
        source_id = path.relative_to(sources_root).as_posix()
        if any(_matches_exclusion(source_id, exclusion) for exclusion in exclusions):
            files_excluded += 1
            continue

        targets.append(ExtractionTarget(source_id, path))

    return tuple(targets), files_found, files_excluded


def _json_from_output(cmd: list[str], input_json: str | None = None) -> dict:
    output_json = run(
        cmd,
        capture_output=True,
        text=True,
        input=input_json,
        check=True,
    ).stdout

    try:
        return json.loads(output_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from output: {output_json}") from e


def _matches_exclusion(source_id: str, exclusion: str) -> bool:
    if fnmatch(source_id, exclusion):
        return True

    normalized = exclusion.strip("/")
    has_glob = any(char in normalized for char in "*?[")
    if not normalized or has_glob:
        return False

    return source_id.startswith(f"{normalized}/")


__all__ = [
    "ExtractionTarget",
    "SourceExtraction",
    "SourceExtractor",
]
