from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FindingSeverity = Literal["error", "attention"]


@dataclass(frozen=True)
class WorkspaceHealthFinding:
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
class WorkspaceHealthReport:
    project_root: Path
    config_path: Path
    config_present: bool
    target_dir_present: bool
    rules_dir_present: bool
    local_rules_dir_present: bool
    shared_rules_dir_present: bool
    recipes_dir_present: bool
    rules_report: object
    recipe_report: object
    findings: tuple[WorkspaceHealthFinding, ...]

    @property
    def blocking_findings(self) -> tuple[WorkspaceHealthFinding, ...]:
        return tuple(
            finding for finding in self.findings if finding.severity == "error"
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "config_path": str(self.config_path) if self.config_path else "",
            "config_present": self.config_present,
            "target_dir_present": self.target_dir_present,
            "rules_dir_present": self.rules_dir_present,
            "local_rules_dir_present": self.local_rules_dir_present,
            "shared_rules_dir_present": self.shared_rules_dir_present,
            "recipes_dir_present": self.recipes_dir_present,
            "findings": [finding.to_json_dict() for finding in self.findings],
        }


__all__ = [
    "FindingSeverity",
    "WorkspaceHealthFinding",
    "WorkspaceHealthReport",
]
