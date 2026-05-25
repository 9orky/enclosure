from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import field_validator

from enclosure.shared import architecture, config, limits

FindingSeverity = Literal["error", "attention"]


class HealthConfig(config.StrictConfigModel):
    top: int

    @field_validator("top")
    @classmethod
    def top_is_limit(cls, value: int) -> int:
        return limits.validate_report_limit(value)


@dataclass(frozen=True)
class HealthFinding:
    severity: FindingSeverity
    category: str
    subject: str
    detail: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "category": self.category,
            "subject": self.subject,
            "detail": self.detail,
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
    top: int = 0
    findings: tuple[HealthFinding, ...] = ()
    hotspots: tuple[HealthHotspotSummary, ...] = ()
    pressure_clusters: tuple[HealthClusterSummary, ...] = ()

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
            "top": self.top,
            "findings": [finding.to_json_dict() for finding in self.findings],
            "hotspots": [hotspot.to_json_dict() for hotspot in self.hotspots],
            "pressure_clusters": [
                cluster.to_json_dict() for cluster in self.pressure_clusters
            ],
        }


__all__ = [
    "ArchitectureHealthReport",
    "HealthConfig",
    "HealthClusterSummary",
    "HealthFinding",
    "HealthHotspotSummary",
]
