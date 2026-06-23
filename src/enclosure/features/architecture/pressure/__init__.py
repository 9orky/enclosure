from __future__ import annotations

from importlib import import_module

from . import domain

ArchitecturePressureReport = domain.ArchitecturePressureReport
CallablePressure = domain.CallablePressure
ExportPressure = domain.ExportPressure
describe_architecture_pressure = domain.describe_architecture_pressure


def build_pressure_report() -> domain.ArchitecturePressureReport:
    application = import_module("enclosure.features.architecture.pressure.application")
    return application.build_pressure_report()


def build_pressure_report_for_top(top: int | None) -> domain.ArchitecturePressureReport:
    application = import_module("enclosure.features.architecture.pressure.application")
    return application.build_pressure_report_for_top(top)

__all__ = [
    "ArchitecturePressureReport",
    "CallablePressure",
    "ExportPressure",
    "build_pressure_report",
    "build_pressure_report_for_top",
    "describe_architecture_pressure",
]
