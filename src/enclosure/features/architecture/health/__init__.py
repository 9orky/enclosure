from __future__ import annotations

from . import application, domain

ArchitectureHealthReport = domain.ArchitectureHealthReport
build_health_report = application.build_health_report
build_health_report_for_top = application.build_health_report_for_top

__all__ = [
    "ArchitectureHealthReport",
    "build_health_report",
    "build_health_report_for_top",
]
