from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FindingSeverity = Literal["error", "attention"]


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
class HealthReport:
    project_root: Path
    workspace: object
    architecture: object
    findings: tuple[HealthFinding, ...]

    @property
    def blocking_findings(self) -> tuple[object, ...]:
        findings: list[object] = [
            finding for finding in self.findings if finding.severity == "error"
        ]
        if self.workspace is not None:
            findings.extend(self.workspace.blocking_findings)
        if self.architecture is not None:
            findings.extend(self.architecture.blocking_findings)
        return tuple(findings)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "findings": [finding.to_json_dict() for finding in self.findings],
            "workspace": (
                self.workspace.to_json_dict() if self.workspace is not None else None
            ),
            "architecture": (
                self.architecture.to_json_dict()
                if self.architecture is not None
                else None
            ),
        }


__all__ = [
    "FindingSeverity",
    "HealthFinding",
    "HealthReport",
]
