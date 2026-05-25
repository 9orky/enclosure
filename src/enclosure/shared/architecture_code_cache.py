from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

import modwire.definitions
import modwire.extraction
import modwire.extractors.base
from modwire.definitions import SourceFile
from modwire.extraction import (
    CodeMap,
    ExtractionResult,
    ExtractionSummary,
)
from modwire.extractors import load_extractor
from modwire.extractors.base import _collect_extraction_targets
from modwire.graph import build_dependency_graph
from pydantic import BaseModel, ConfigDict, ValidationError

from enclosure.shared import layout

CACHE_SCHEMA_VERSION = 1
CACHE_NAMESPACE = "modwire"
MAX_CACHE_ENTRIES = 3


class _CacheModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImplementationFileStamp(_CacheModel):
    path: str
    size: int
    mtime_ns: int


class RuntimeStamp(_CacheModel):
    command: str
    executable: str
    size: int = -1
    mtime_ns: int = -1


class ArchitectureCodeCacheKey(_CacheModel):
    schema_version: int
    language: str
    project_root: str
    exclusions: tuple[str, ...]
    python_version: str
    runtime: RuntimeStamp
    implementation_files: tuple[ImplementationFileStamp, ...]


class SourceFileStamp(_CacheModel):
    path: str
    size: int
    mtime_ns: int


class SourceManifest(_CacheModel):
    files_found: int
    files_excluded: int
    files_checked: int
    files: tuple[SourceFileStamp, ...]


class ExtractionSummarySnapshot(_CacheModel):
    files_found: int
    files_checked: int
    files_excluded: int


class ArchitectureCodeCacheEntry(_CacheModel):
    schema_version: int
    key: ArchitectureCodeCacheKey
    source_manifest: SourceManifest
    summary: ExtractionSummarySnapshot
    runtime_command: str
    files: dict[str, SourceFile]


ExtractCode = Callable[[str, Path, tuple[str, ...]], CodeMap]


def extract_with_cache(
    *,
    language: str,
    project_root: Path,
    exclusions: tuple[str, ...],
    extract_code: ExtractCode,
    cache_root: Path | None = None,
) -> CodeMap:
    if not project_root.is_dir():
        return extract_code(language, project_root, exclusions)

    active_cache_root = cache_root or project_root
    try:
        cache_key = _cache_key(language, project_root, exclusions)
        source_manifest = _source_manifest(language, project_root, exclusions)
    except Exception:
        return extract_code(language, project_root, exclusions)

    cache_path = _cache_path(active_cache_root, cache_key)
    cached_code_map = _read_code_map(cache_path, cache_key, source_manifest)
    if cached_code_map is not None:
        return cached_code_map

    code_map = extract_code(language, project_root, exclusions)
    try:
        refreshed_manifest = _source_manifest(language, project_root, exclusions)
    except Exception:
        return code_map

    if refreshed_manifest == source_manifest:
        _write_code_map(cache_path, cache_key, refreshed_manifest, code_map)
    return code_map


def _read_code_map(
    cache_path: Path,
    cache_key: ArchitectureCodeCacheKey,
    source_manifest: SourceManifest,
) -> CodeMap | None:
    try:
        entry = ArchitectureCodeCacheEntry.model_validate_json(
            cache_path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, ValueError):
        return None

    if entry.schema_version != CACHE_SCHEMA_VERSION:
        return None
    if entry.key != cache_key:
        return None
    if entry.source_manifest != source_manifest:
        return None

    return _code_map_from_entry(entry)


def _write_code_map(
    cache_path: Path,
    cache_key: ArchitectureCodeCacheKey,
    source_manifest: SourceManifest,
    code_map: CodeMap,
) -> None:
    summary = code_map.extraction_result.summary
    entry = ArchitectureCodeCacheEntry(
        schema_version=CACHE_SCHEMA_VERSION,
        key=cache_key,
        source_manifest=source_manifest,
        summary=ExtractionSummarySnapshot(
            files_found=summary.files_found,
            files_checked=summary.files_checked,
            files_excluded=summary.files_excluded,
        ),
        runtime_command=code_map.runtime_command,
        files=dict(code_map.extraction_result.files),
    )

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = cache_path.with_name(
            f".{cache_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        )
        with temporary_path.open("w", encoding="utf-8") as cache_file:
            cache_file.write(entry.model_dump_json(indent=2))
            cache_file.write("\n")
            cache_file.flush()
            os.fsync(cache_file.fileno())
        os.replace(temporary_path, cache_path)
    except OSError:
        return

    _fsync_parent(cache_path.parent)
    _prune_cache_entries(cache_path.parent, keep_path=cache_path)


def _code_map_from_entry(entry: ArchitectureCodeCacheEntry) -> CodeMap:
    files = dict(entry.files)
    return CodeMap(
        graph=build_dependency_graph(files),
        extraction_result=ExtractionResult(
            files=files,
            summary=ExtractionSummary(
                files_found=entry.summary.files_found,
                files_checked=entry.summary.files_checked,
                files_excluded=entry.summary.files_excluded,
            ),
        ),
        runtime_command=entry.runtime_command,
    )


def _cache_path(project_root: Path, cache_key: ArchitectureCodeCacheKey) -> Path:
    key_json = json.dumps(
        cache_key.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    key_hash = hashlib.sha256(key_json.encode("utf-8")).hexdigest()
    return (
        layout.current_layout().cache_dir(project_root)
        / CACHE_NAMESPACE
        / f"{key_hash}.json"
    )


def _cache_key(
    language: str,
    project_root: Path,
    exclusions: tuple[str, ...],
) -> ArchitectureCodeCacheKey:
    extractor = load_extractor(language)
    return ArchitectureCodeCacheKey(
        schema_version=CACHE_SCHEMA_VERSION,
        language=language,
        project_root=str(project_root.resolve()),
        exclusions=tuple(sorted(exclusion.strip() for exclusion in exclusions)),
        python_version=sys.version,
        runtime=_runtime_stamp(extractor.command),
        implementation_files=_implementation_file_stamps(extractor),
    )


def _source_manifest(
    language: str,
    project_root: Path,
    exclusions: tuple[str, ...],
) -> SourceManifest:
    extractor = load_extractor(language)
    targets, files_found, files_excluded = _collect_extraction_targets(
        project_root,
        extractor.file_extensions,
        exclusions,
    )
    return SourceManifest(
        files_found=files_found,
        files_excluded=files_excluded,
        files_checked=len(targets),
        files=tuple(
            _source_file_stamp(target.source_id, target.path)
            for target in targets
        ),
    )


def _implementation_file_stamps(
    extractor: object,
) -> tuple[ImplementationFileStamp, ...]:
    paths = (
        Path(inspect.getfile(type(extractor))),
        Path(modwire.definitions.__file__),
        Path(modwire.extraction.__file__),
        Path(__file__),
        Path(modwire.extractors.base.__file__).parent
        / "scripts"
        / getattr(extractor, "extractor_file"),
    )
    return tuple(
        stamp
        for path in paths
        if (stamp := _implementation_file_stamp(path)) is not None
    )


def _source_file_stamp(source_id: str, path: Path) -> SourceFileStamp:
    stat_result = path.stat()
    return SourceFileStamp(
        path=source_id,
        size=stat_result.st_size,
        mtime_ns=stat_result.st_mtime_ns,
    )


def _implementation_file_stamp(path: Path) -> ImplementationFileStamp | None:
    try:
        stat_result = path.stat()
    except OSError:
        return None
    return ImplementationFileStamp(
        path=str(path.resolve()),
        size=stat_result.st_size,
        mtime_ns=stat_result.st_mtime_ns,
    )


def _runtime_stamp(command: str) -> RuntimeStamp:
    executable = shutil.which(command) or command
    try:
        stat_result = Path(executable).stat()
    except OSError:
        return RuntimeStamp(command=command, executable=executable)
    return RuntimeStamp(
        command=command,
        executable=str(Path(executable).resolve()),
        size=stat_result.st_size,
        mtime_ns=stat_result.st_mtime_ns,
    )


def _fsync_parent(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _prune_cache_entries(cache_dir: Path, *, keep_path: Path) -> None:
    entry_limit = max(1, MAX_CACHE_ENTRIES)
    try:
        cache_entries = tuple(
            path
            for path in cache_dir.glob("*.json")
            if path.is_file()
        )
    except OSError:
        return

    if len(cache_entries) <= entry_limit:
        return

    removable_entries = tuple(
        path
        for path in cache_entries
        if path.resolve(strict=False) != keep_path.resolve(strict=False)
    )
    excess_count = len(cache_entries) - entry_limit
    for cache_entry in sorted(removable_entries, key=_cache_entry_age)[:excess_count]:
        try:
            cache_entry.unlink()
        except OSError:
            pass


def _cache_entry_age(path: Path) -> tuple[int, str]:
    try:
        return path.stat().st_mtime_ns, path.name
    except OSError:
        return -1, path.name


__all__ = [
    "extract_with_cache",
]
