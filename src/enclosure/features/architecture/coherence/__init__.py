from __future__ import annotations

from importlib import import_module

from . import domain

ArchitectureCoherenceReport = domain.ArchitectureCoherenceReport
CoherenceAxisScore = domain.CoherenceAxisScore
CoherenceFinding = domain.CoherenceFinding
CoherenceStream = domain.CoherenceStream
describe_coherence = domain.describe_coherence


def build_coherence_report() -> domain.ArchitectureCoherenceReport:
    application = import_module("enclosure.features.architecture.coherence.application")
    return application.build_coherence_report()


def build_coherence_report_for_top(
    top: int | None,
) -> domain.ArchitectureCoherenceReport:
    application = import_module("enclosure.features.architecture.coherence.application")
    return application.build_coherence_report_for_top(top)


__all__ = [
    "ArchitectureCoherenceReport",
    "CoherenceAxisScore",
    "CoherenceFinding",
    "CoherenceStream",
    "build_coherence_report",
    "build_coherence_report_for_top",
    "describe_coherence",
]
