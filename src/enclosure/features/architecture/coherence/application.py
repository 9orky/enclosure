from __future__ import annotations

from enclosure.shared import architecture_code, limits

from . import domain


def build_coherence_report() -> domain.ArchitectureCoherenceReport:
    return _build_coherence_report(top_override=None)


def build_coherence_report_for_top(
    top: int | None,
) -> domain.ArchitectureCoherenceReport:
    return _build_coherence_report(top_override=top)


def _build_coherence_report(
    top_override: int | None,
) -> domain.ArchitectureCoherenceReport:
    code_analysis = architecture_code.extract_architecture_code()
    config = code_analysis.config
    top = limits.validate_report_limit(
        config.health.top if top_override is None else top_override
    )
    described = domain.describe_coherence(
        code_analysis.code_map,
        code_analysis.matching_config,
        top,
    )
    return domain.ArchitectureCoherenceReport(
        **code_analysis.report_fields(),
        top=top,
        stream_count=described.stream_count,
        finding_count=described.finding_count,
        streams=described.streams,
        findings=described.findings,
    )


__all__ = [
    "build_coherence_report",
    "build_coherence_report_for_top",
]
