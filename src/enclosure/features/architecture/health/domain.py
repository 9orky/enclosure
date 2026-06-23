from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Literal

from enclosure.shared import architecture

FindingSeverity = Literal["error", "attention"]


def _action_kind_for(severity: FindingSeverity, category: str) -> str:
    if severity == "error":
        return "blocker"
    return "investigate"


def _next_step_for(severity: FindingSeverity, category: str) -> str:
    if category == "boundaries":
        return "Run `enclosure architecture boundaries`."
    if category == "shape":
        return "Run `enclosure architecture shape`."
    if category == "map":
        return "Run `enclosure architecture map`."
    if category == "pressure":
        return "Run `enclosure architecture pressure`."
    if category == "coherence":
        return "Run `enclosure architecture coherence`."
    if category == "clusters":
        return "Run `enclosure architecture clusters`."
    if severity == "error":
        return "Fix this before review."
    return "Investigate when this area is in scope."


@dataclass(frozen=True)
class HealthFinding:
    severity: FindingSeverity
    category: str
    subject: str
    detail: str

    @property
    def action_kind(self) -> str:
        return _action_kind_for(self.severity, self.category)

    @property
    def next_step(self) -> str:
        return _next_step_for(self.severity, self.category)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "action_kind": self.action_kind,
            "category": self.category,
            "subject": self.subject,
            "detail": self.detail,
            "next_step": self.next_step,
        }


@dataclass(frozen=True)
class HealthClusterSummary:
    name: str
    pressure_score: float
    file_count: int
    incoming_edges: int
    outgoing_edges: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "pressure_score": self.pressure_score,
            "file_count": self.file_count,
            "incoming_edges": self.incoming_edges,
            "outgoing_edges": self.outgoing_edges,
        }


@dataclass(frozen=True)
class HealthHotspotSummary:
    kind: str
    name: str
    detail: str
    score: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "name": self.name,
            "detail": self.detail,
            "score": self.score,
        }


@dataclass(frozen=True)
class ArchitectureHealthReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    boundary_violation_count: int = 0
    shape_violation_count: int = 0
    unknown_file_count: int = 0
    module_count: int = 0
    cross_module_dependency_count: int = 0
    cluster_count: int = 0
    callable_count: int = 0
    call_count: int = 0
    unresolved_call_count: int = 0
    unresolved_internal_call_count: int = 0
    unresolved_non_actionable_call_count: int = 0
    coherence_stream_count: int = 0
    coherence_finding_count: int = 0
    cluster_group_depth: int = 0
    cluster_files_top: int = 0
    top: int = 0
    findings: tuple[HealthFinding, ...] = ()
    hotspots: tuple[HealthHotspotSummary, ...] = ()
    pressure_clusters: tuple[HealthClusterSummary, ...] = ()
    boundary_violations: tuple[object, ...] = field(default_factory=tuple)
    shape_violations: tuple[object, ...] = field(default_factory=tuple)
    modules: tuple[object, ...] = field(default_factory=tuple)
    dependencies: tuple[object, ...] = field(default_factory=tuple)
    unknown_files: tuple[str, ...] = ()
    clusters: tuple[object, ...] = field(default_factory=tuple)
    most_calling: tuple[object, ...] = field(default_factory=tuple)
    most_called: tuple[object, ...] = field(default_factory=tuple)
    wide_signatures: tuple[object, ...] = field(default_factory=tuple)
    reexport_hubs: tuple[object, ...] = field(default_factory=tuple)
    public_api_hubs: tuple[object, ...] = field(default_factory=tuple)
    coherence_streams: tuple[object, ...] = field(default_factory=tuple)
    coherence_findings: tuple[object, ...] = field(default_factory=tuple)

    @property
    def blocking_findings(self) -> tuple[HealthFinding, ...]:
        return tuple(
            finding for finding in self.findings if finding.severity == "error"
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "boundary_violation_count": self.boundary_violation_count,
            "shape_violation_count": self.shape_violation_count,
            "unknown_file_count": self.unknown_file_count,
            "module_count": self.module_count,
            "cross_module_dependency_count": self.cross_module_dependency_count,
            "cluster_count": self.cluster_count,
            "callable_count": self.callable_count,
            "call_count": self.call_count,
            "unresolved_call_count": self.unresolved_call_count,
            "unresolved_internal_call_count": self.unresolved_internal_call_count,
            "unresolved_non_actionable_call_count": (
                self.unresolved_non_actionable_call_count
            ),
            "coherence_stream_count": self.coherence_stream_count,
            "coherence_finding_count": self.coherence_finding_count,
            "cluster_group_depth": self.cluster_group_depth,
            "cluster_files_top": self.cluster_files_top,
            "top": self.top,
            "findings": [finding.to_json_dict() for finding in self.findings],
            "hotspots": [hotspot.to_json_dict() for hotspot in self.hotspots],
            "pressure_clusters": [
                cluster.to_json_dict() for cluster in self.pressure_clusters
            ],
            "boundary_violations": [
                _json_dict(violation) for violation in self.boundary_violations
            ],
            "shape_violations": [
                _json_dict(violation) for violation in self.shape_violations
            ],
            "modules": [_json_dict(module) for module in self.modules],
            "dependencies": [
                _json_dict(dependency) for dependency in self.dependencies
            ],
            "unknown_files": list(self.unknown_files),
            "clusters": [_json_dict(cluster) for cluster in self.clusters],
            "most_calling": [_json_dict(pressure) for pressure in self.most_calling],
            "most_called": [_json_dict(pressure) for pressure in self.most_called],
            "wide_signatures": [
                _json_dict(pressure) for pressure in self.wide_signatures
            ],
            "reexport_hubs": [
                _json_dict(pressure) for pressure in self.reexport_hubs
            ],
            "public_api_hubs": [
                _json_dict(pressure) for pressure in self.public_api_hubs
            ],
            "coherence_streams": [
                _json_dict(stream) for stream in self.coherence_streams
            ],
            "coherence_findings": [
                _json_dict(finding) for finding in self.coherence_findings
            ],
        }


def _json_dict(value: object) -> dict[str, object]:
    if hasattr(value, "to_json_dict"):
        return value.to_json_dict()
    if is_dataclass(value):
        return asdict(value)
    return {"value": str(value)}


__all__ = [
    "ArchitectureHealthReport",
    "HealthClusterSummary",
    "HealthFinding",
    "HealthHotspotSummary",
]
