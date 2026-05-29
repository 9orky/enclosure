from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from enclosure.shared import architecture

AxisName = Literal[
    "naming",
    "tree_shape",
    "sibling_pattern",
    "flow",
    "seam_use",
    "dependency_pressure",
    "configuration",
]

STREAM_AXES: tuple[AxisName, ...] = (
    "naming",
    "tree_shape",
    "sibling_pattern",
    "flow",
    "seam_use",
    "dependency_pressure",
)


@dataclass(frozen=True)
class CoherenceFinding:
    stream: str
    axis: AxisName
    subject: str
    detail: str
    evidence: str
    impact: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "stream": self.stream,
            "axis": self.axis,
            "subject": self.subject,
            "detail": self.detail,
            "evidence": self.evidence,
            "impact": self.impact,
        }


@dataclass(frozen=True)
class CoherenceAxisScore:
    axis: AxisName
    score: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "axis": self.axis,
            "score": self.score,
        }


@dataclass(frozen=True)
class CoherenceStream:
    name: str
    source_count: int
    axis_scores: tuple[CoherenceAxisScore, ...]
    findings: tuple[CoherenceFinding, ...]

    @property
    def axis_summary(self) -> str:
        return ", ".join(
            f"{score.axis.replace('_', '-')} {score.score}"
            for score in self.axis_scores
        )

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def lowest_score(self) -> int:
        scores = tuple(score.score for score in self.axis_scores)
        return min(scores) if scores else 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source_count": self.source_count,
            "axis_scores": [score.to_json_dict() for score in self.axis_scores],
            "findings": [finding.to_json_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class DescribedCoherence:
    stream_count: int
    finding_count: int
    streams: tuple[CoherenceStream, ...]
    findings: tuple[CoherenceFinding, ...]


@dataclass(frozen=True)
class ArchitectureCoherenceReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    top: int = 0
    stream_count: int = 0
    finding_count: int = 0
    streams: tuple[CoherenceStream, ...] = ()
    findings: tuple[CoherenceFinding, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "top": self.top,
            "stream_count": self.stream_count,
            "finding_count": self.finding_count,
            "streams": [stream.to_json_dict() for stream in self.streams],
            "findings": [finding.to_json_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class FileMap:
    source_id: str
    stream: str
    layer: str
    layer_root: str
    is_api: bool
    root_part: str
    parts: tuple[str, ...]


@dataclass(frozen=True)
class ImportTarget:
    stream: str
    source_id: str
    is_api: bool


__all__ = [
    "ArchitectureCoherenceReport",
    "AxisName",
    "CoherenceAxisScore",
    "CoherenceFinding",
    "CoherenceStream",
    "DescribedCoherence",
    "FileMap",
    "ImportTarget",
    "STREAM_AXES",
]
