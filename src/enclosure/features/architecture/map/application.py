from __future__ import annotations

from enclosure.shared import architecture_code, limits

from . import domain


def build_map_report() -> domain.ArchitectureMapReport:
    return _build_map_report(top_override=None)


def build_map_report_for_top(top: int | None) -> domain.ArchitectureMapReport:
    return _build_map_report(top_override=top)


def _build_map_report(top_override: int | None) -> domain.ArchitectureMapReport:
    code_analysis = architecture_code.extract_architecture_code()
    config = code_analysis.config
    code_map = code_analysis.code_map
    top = limits.validate_report_limit(
        config.map.top if top_override is None else top_override
    )
    mapped = domain.describe_architecture_map(
        code_map.graph,
        code_analysis.matching_config,
        tracked_files=tuple(code_map.extraction_result.files),
        top=top,
    )
    return domain.ArchitectureMapReport(
        **code_analysis.report_fields(),
        modules=mapped.modules,
        dependencies=mapped.dependencies,
        unknown_files=mapped.unknown_files,
        hotspots=mapped.hotspots,
        top=top,
    )


__all__ = [
    "build_map_report",
    "build_map_report_for_top",
]
