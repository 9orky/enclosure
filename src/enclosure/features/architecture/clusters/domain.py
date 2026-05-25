from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import PurePosixPath
from pathlib import Path

from modwire import CodeMap
from pydantic import Field, field_validator

from enclosure.shared import architecture, config, limits


class ClustersConfig(config.StrictConfigModel):
    group_depth: int = Field(ge=1, le=8)
    top: int
    files_top: int

    @field_validator("top", "files_top")
    @classmethod
    def value_is_limit(cls, value: int) -> int:
        return limits.validate_report_limit(value)


@dataclass(frozen=True)
class ClusterFile:
    path: str
    imports_count: int
    imported_by_count: int
    symbol_count: int
    public_symbol_count: int
    line_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "imports_count": self.imports_count,
            "imported_by_count": self.imported_by_count,
            "symbol_count": self.symbol_count,
            "public_symbol_count": self.public_symbol_count,
            "line_count": self.line_count,
        }


@dataclass(frozen=True)
class ArchitectureCluster:
    name: str
    file_count: int
    line_count: int
    public_symbol_count: int
    imports_count: int
    imported_by_count: int
    internal_edges: int
    incoming_edges: int
    outgoing_edges: int
    external_imports: int
    pressure_score: float
    dependencies: tuple[str, ...]
    dependents: tuple[str, ...]
    files: tuple[ClusterFile, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "file_count": self.file_count,
            "line_count": self.line_count,
            "public_symbol_count": self.public_symbol_count,
            "imports_count": self.imports_count,
            "imported_by_count": self.imported_by_count,
            "internal_edges": self.internal_edges,
            "incoming_edges": self.incoming_edges,
            "outgoing_edges": self.outgoing_edges,
            "external_imports": self.external_imports,
            "pressure_score": self.pressure_score,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "files": [file.to_json_dict() for file in self.files],
        }


@dataclass(frozen=True)
class ClustersReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    group_depth: int
    top: int
    files_top: int
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    clusters: tuple[ArchitectureCluster, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "group_depth": self.group_depth,
            "top": self.top,
            "files_top": self.files_top,
            "clusters": [cluster.to_json_dict() for cluster in self.clusters],
        }


def describe_clusters(
    code_map: CodeMap,
    *,
    group_depth: int,
) -> tuple[ArchitectureCluster, ...]:
    tracked_files = code_map.extraction_result.files
    incoming_by_file = _incoming_counts(code_map, set(tracked_files))
    cluster_by_file = {
        path: _cluster_name(path, group_depth) for path in tracked_files
    }
    builders: dict[str, _ClusterBuilder] = defaultdict(_ClusterBuilder)

    for path, source_file in tracked_files.items():
        builders[cluster_by_file[path]].add_file(
            ClusterFile(
                path=path,
                imports_count=len(source_file.imports),
                imported_by_count=incoming_by_file[path],
                symbol_count=len(source_file.classes) + len(source_file.functions),
                public_symbol_count=source_file.public_symbol_count,
                line_count=source_file.line_count,
            )
        )

    for edge in code_map.graph.edges:
        if edge.from_id not in tracked_files:
            continue

        source_cluster = cluster_by_file[edge.from_id]
        source = builders[source_cluster]
        if edge.to_id not in tracked_files:
            source.external_imports += 1
            continue

        target_cluster = cluster_by_file[edge.to_id]
        if source_cluster == target_cluster:
            source.internal_edges += 1
            continue

        source.outgoing_edges += 1
        source.dependencies.add(target_cluster)
        target = builders[target_cluster]
        target.incoming_edges += 1
        target.dependents.add(source_cluster)

    return tuple(
        sorted(
            (
                builder.build(name)
                for name, builder in builders.items()
            ),
            key=lambda cluster: (
                -cluster.pressure_score,
                -cluster.file_count,
                cluster.name,
            ),
        )
    )


def _incoming_counts(code_map: CodeMap, tracked_files: set[str]) -> dict[str, int]:
    incoming = dict.fromkeys(tracked_files, 0)
    for edge in code_map.graph.edges:
        if edge.from_id in tracked_files and edge.to_id in tracked_files:
            incoming[edge.to_id] += 1
    return incoming


def _cluster_name(path: str, group_depth: int) -> str:
    parts = PurePosixPath(path).parts
    if not parts:
        return "."
    prefix_size = min(max(group_depth, 1), max(len(parts) - 1, 1))
    return "/".join(parts[:prefix_size])


@dataclass
class _ClusterBuilder:
    files: list[ClusterFile] = field(default_factory=list)
    internal_edges: int = 0
    incoming_edges: int = 0
    outgoing_edges: int = 0
    external_imports: int = 0
    dependencies: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)

    def add_file(self, file: ClusterFile) -> None:
        self.files.append(file)

    def build(self, name: str) -> ArchitectureCluster:
        files = tuple(
            sorted(
                self.files,
                key=lambda file: (
                    -(file.imported_by_count + file.imports_count),
                    -file.line_count,
                    file.path,
                ),
            )
        )
        pressure_score = (
            (self.incoming_edges * 2.0)
            + (self.outgoing_edges * 1.5)
            + (self.internal_edges * 0.5)
            + (self.external_imports * 0.25)
            + (len(files) * 0.25)
        )
        return ArchitectureCluster(
            name=name,
            file_count=len(files),
            line_count=sum(file.line_count for file in files),
            public_symbol_count=sum(file.public_symbol_count for file in files),
            imports_count=sum(file.imports_count for file in files),
            imported_by_count=sum(file.imported_by_count for file in files),
            internal_edges=self.internal_edges,
            incoming_edges=self.incoming_edges,
            outgoing_edges=self.outgoing_edges,
            external_imports=self.external_imports,
            pressure_score=round(pressure_score, 2),
            dependencies=tuple(sorted(self.dependencies)),
            dependents=tuple(sorted(self.dependents)),
            files=files,
        )


__all__ = [
    "ArchitectureCluster",
    "ClusterFile",
    "ClustersConfig",
    "ClustersReport",
    "describe_clusters",
]
