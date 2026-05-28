from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modwire import CodeMap, extract_code
from modwire.definitions import SourceFile, SourceImport
from modwire.extraction import ExtractionResult, ExtractionSummary
from modwire.graph import DependencyGraph, build_dependency_graph

from enclosure.shared import architecture_code_cache, config

DEFAULT_ARCHITECTURE_EXCLUSIONS = (
    ".dev/**",
    ".git/**",
    "build/**",
    "dist/**",
    "__pycache__/**",
)


@dataclass(frozen=True)
class ArchitectureCodeMap:
    project_root: Path
    config_path: Path
    config: object
    matching_config: object
    code_map: CodeMap

    def report_fields(self) -> dict[str, object]:
        summary = self.code_map.extraction_result.summary
        language = getattr(self.config, "language")
        return {
            "project_root": self.project_root,
            "config_path": self.config_path,
            "config_format": self.config_path.suffix.lstrip("."),
            "language": language,
            "runtime_command": self.code_map.runtime_command,
            "files_found": summary.files_found,
            "files_excluded": summary.files_excluded,
            "files_checked": summary.files_checked,
        }


def extract_architecture_code() -> ArchitectureCodeMap:
    from enclosure.features.architecture.config import domain

    project_root, config_path, raw_data = config.load_project_mapping()
    architecture_config = domain.ArchitectureConfig.validate_mapping(
        raw_data,
        config_path,
    )
    architecture_root = _architecture_root(project_root, architecture_config)
    code_map = architecture_code_cache.extract_with_cache(
        language=architecture_config.language,
        project_root=architecture_root,
        exclusions=_extraction_exclusions(
            project_root,
            architecture_root,
            architecture_config,
        ),
        extract_code=extract_code,
        cache_root=project_root,
    )
    return ArchitectureCodeMap(
        project_root=project_root,
        config_path=config_path,
        config=architecture_config,
        matching_config=_matching_config(architecture_config),
        code_map=code_map,
    )


def tracked_dependency_graph(code_map: CodeMap) -> DependencyGraph:
    tracked_files = set(code_map.extraction_result.files)
    graph = DependencyGraph()
    for source_id in tracked_files:
        graph.add_node(source_id)
    for edge in code_map.graph.edges:
        if edge.from_id in tracked_files and edge.to_id in tracked_files:
            graph.add_edge(edge.from_id, edge.to_id, kind=edge.kind)
    return graph


def _architecture_root(project_root: Path, architecture_config: object) -> Path:
    configured_root = getattr(architecture_config, "architecture_root", "")
    if not configured_root:
        return project_root

    root_path = Path(str(configured_root)).expanduser()
    if not root_path.is_absolute():
        root_path = project_root / root_path
    return root_path.resolve(strict=False)


def _extraction_exclusions(
    project_root: Path,
    architecture_root: Path,
    architecture_config: object,
) -> tuple[str, ...]:
    exclusions = tuple(getattr(architecture_config, "exclusions", ()))
    if not getattr(architecture_config, "architecture_root", ""):
        return exclusions

    source_prefix = _source_prefix(project_root, architecture_root)
    return _rooted_exclusions(
        tuple(dict.fromkeys((*exclusions, *DEFAULT_ARCHITECTURE_EXCLUSIONS))),
        source_prefix,
    )


def _rooted_exclusions(
    exclusions: tuple[str, ...],
    source_prefix: str,
) -> tuple[str, ...]:
    normalized_prefix = source_prefix.strip("/")
    rooted_exclusions: list[str] = []
    for exclusion in exclusions:
        normalized = exclusion.strip().strip("/")
        if not normalized:
            continue
        rooted_exclusions.append(normalized)
        stripped = _strip_source_prefix(normalized, normalized_prefix)
        if stripped and stripped != normalized:
            rooted_exclusions.append(stripped)
    return tuple(dict.fromkeys(rooted_exclusions))


def _strip_source_prefix(exclusion: str, source_prefix: str) -> str:
    if not source_prefix:
        return exclusion
    if exclusion == source_prefix:
        return "**"
    if exclusion.startswith(f"{source_prefix}/"):
        stripped = exclusion[len(source_prefix) + 1 :].strip("/")
        return stripped or "**"
    return exclusion


def _source_prefix(project_root: Path, architecture_root: Path) -> str:
    try:
        prefix = (
            architecture_root.resolve(strict=False)
            .relative_to(project_root.resolve(strict=False))
            .as_posix()
            .strip("/")
        )
    except ValueError:
        return ""
    return "" if prefix == "." else prefix


def _rebase_source_id(source_id: str, prefix: str) -> str | None:
    normalized = source_id.strip("/")
    if not prefix:
        return normalized
    if normalized == prefix:
        return ""
    if normalized.startswith(f"{prefix}/"):
        return normalized[len(prefix) + 1 :]
    return None


def _rebase_import(
    source_import: SourceImport,
    prefix: str,
    known_source_ids: set[str],
) -> SourceImport:
    normalized_path = (
        _rebase_source_id(source_import.normalized_path, prefix)
        or source_import.normalized_path.strip("/")
    )
    join_key = _rebase_source_id(source_import.join_key, prefix)
    return source_import.model_copy(
        update={
            "normalized_path": normalized_path,
            "join_key": join_key if join_key is not None else source_import.join_key,
            "file_barrier_crossed": normalized_path in known_source_ids,
        }
    )


def _scoped_code_map(
    code_map: CodeMap,
    prefix: str,
) -> CodeMap:
    files_by_source_id: dict[str, SourceFile] = {}
    for source_id, source_file in code_map.extraction_result.files.items():
        scoped_source_id = _rebase_source_id(source_id, prefix)
        if not scoped_source_id:
            continue
        files_by_source_id[scoped_source_id] = source_file

    known_source_ids = set(files_by_source_id)
    scoped_files = {
        source_id: source_file.model_copy(
            update={
                "imports": [
                    _rebase_import(source_import, prefix, known_source_ids)
                    for source_import in source_file.imports
                ]
            }
        )
        for source_id, source_file in files_by_source_id.items()
    }
    return CodeMap(
        graph=build_dependency_graph(scoped_files),
        extraction_result=ExtractionResult(
            files=scoped_files,
            summary=ExtractionSummary(
                files_found=len(scoped_files),
                files_checked=len(scoped_files),
                files_excluded=0,
            ),
        ),
        runtime_command=code_map.runtime_command,
    )


class _ArchitectureMatchingConfig:
    def __init__(self, architecture_config: object) -> None:
        self._architecture_config = architecture_config

    @property
    def architecture_root(self) -> str:
        return ""

    def __getattr__(self, name: str) -> object:
        return getattr(self._architecture_config, name)


def _matching_config(architecture_config: object) -> object:
    if not getattr(architecture_config, "architecture_root", ""):
        return architecture_config
    return _ArchitectureMatchingConfig(architecture_config)


__all__ = [
    "ArchitectureCodeMap",
    "extract_architecture_code",
    "tracked_dependency_graph",
]
