from __future__ import annotations

from importlib import import_module

from . import domain

HealthFinding = domain.HealthFinding
HealthReport = domain.HealthReport


def build_health_report() -> domain.HealthReport:
    application = import_module("enclosure.features.health.report.application")
    return application.build_health_report()


def build_health_report_for_top(top: int | None) -> domain.HealthReport:
    application = import_module("enclosure.features.health.report.application")
    return application.build_health_report_for_top(top)

__all__ = [
    "HealthFinding",
    "HealthReport",
    "build_health_report",
    "build_health_report_for_top",
]
