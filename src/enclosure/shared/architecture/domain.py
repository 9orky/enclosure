from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ArchitectureReportMetadata(Protocol):
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str
    files_found: int
    files_excluded: int
    files_checked: int


def metadata_json(report: ArchitectureReportMetadata) -> dict[str, object]:
    return {
        "project_root": str(report.project_root),
        "config_path": str(report.config_path),
        "config_format": report.config_format,
        "language": report.language,
        "runtime_command": report.runtime_command,
        "files_found": report.files_found,
        "files_excluded": report.files_excluded,
        "files_checked": report.files_checked,
    }


def scan_summary(report: ArchitectureReportMetadata) -> str:
    return "\n".join(
        (
            f"- Paths found in scope: {report.files_found}",
            f"- Paths excluded by rules: {report.files_excluded}",
            f"- Files checked: {report.files_checked}",
        )
    )


__all__ = [
    "ArchitectureReportMetadata",
    "metadata_json",
    "scan_summary",
]
