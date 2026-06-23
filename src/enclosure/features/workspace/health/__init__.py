from __future__ import annotations

from . import application, domain

WorkspaceHealthFinding = domain.WorkspaceHealthFinding
WorkspaceHealthReport = domain.WorkspaceHealthReport
build_workspace_health_report = application.build_workspace_health_report

__all__ = [
    "WorkspaceHealthFinding",
    "WorkspaceHealthReport",
    "build_workspace_health_report",
]
