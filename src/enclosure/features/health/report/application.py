from __future__ import annotations

import enclosure.features.architecture.health
import enclosure.features.workspace.health
from enclosure.shared import layout

from . import domain


def build_health_report() -> domain.HealthReport:
    return build_health_report_for_top(None)


def build_health_report_for_top(top: int | None) -> domain.HealthReport:
    project_root = layout.current_project_root()
    findings: list[domain.HealthFinding] = []
    workspace_report = None
    architecture_report = None

    try:
        workspace_report = (
            enclosure.features.workspace.health.build_workspace_health_report()
        )
    except Exception as exc:
        findings.append(
            domain.HealthFinding(
                severity="error",
                category="workspace",
                subject="workspace health",
                detail=str(exc),
            )
        )

    try:
        architecture_report = (
            enclosure.features.architecture.health.build_health_report_for_top(top)
        )
    except Exception as exc:
        findings.append(
            domain.HealthFinding(
                severity="error",
                category="architecture",
                subject="architecture health",
                detail=str(exc),
            )
        )

    return domain.HealthReport(
        project_root=project_root,
        workspace=workspace_report,
        architecture=architecture_report,
        findings=tuple(findings),
    )


__all__ = [
    "build_health_report",
    "build_health_report_for_top",
]
