from __future__ import annotations

from importlib import import_module

from . import domain

ArchitectureHealthReport = domain.ArchitectureHealthReport


def build_health_report() -> domain.ArchitectureHealthReport:
    application = import_module("enclosure.features.architecture.health.application")
    return application.build_health_report()


def build_health_report_for_top(top: int | None) -> domain.ArchitectureHealthReport:
    application = import_module("enclosure.features.architecture.health.application")
    return application.build_health_report_for_top(top)

__all__ = [
    "ArchitectureHealthReport",
    "build_health_report",
    "build_health_report_for_top",
]
