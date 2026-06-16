from __future__ import annotations

from enclosure.shared import architecture_code, limits

from . import domain

def build_pressure_report() -> domain.ArchitecturePressureReport:
    return build_pressure_report_for_top(None)


def build_pressure_report_for_top(top: int | None) -> domain.ArchitecturePressureReport:
    code_analysis = architecture_code.extract_architecture_code()
    configured_top = getattr(code_analysis.config, "pressure").top
    checked_top = limits.validate_report_limit(configured_top if top is None else top)
    described = domain.describe_architecture_pressure(
        code_analysis.code_map,
        top=checked_top,
    )
    return domain.ArchitecturePressureReport(
        **code_analysis.report_fields(),
        top=checked_top,
        callable_count=described.callable_count,
        call_count=described.call_count,
        resolved_call_count=described.resolved_call_count,
        unresolved_call_count=described.unresolved_call_count,
        unresolved_call_breakdown=described.unresolved_call_breakdown,
        most_calling=described.most_calling,
        most_called=described.most_called,
        wide_signatures=described.wide_signatures,
        reexport_hubs=described.reexport_hubs,
        public_api_hubs=described.public_api_hubs,
    )


__all__ = [
    "build_pressure_report",
    "build_pressure_report_for_top",
]
