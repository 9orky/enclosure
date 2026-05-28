from __future__ import annotations

from importlib import import_module

from . import domain

WorkspaceHealthFinding = domain.WorkspaceHealthFinding
WorkspaceHealthReport = domain.WorkspaceHealthReport


def build_workspace_health_report() -> domain.WorkspaceHealthReport:
    application = import_module("enclosure.features.workspace.health.application")
    return application.build_workspace_health_report()

__all__ = [
    "WorkspaceHealthFinding",
    "WorkspaceHealthReport",
    "build_workspace_health_report",
]
