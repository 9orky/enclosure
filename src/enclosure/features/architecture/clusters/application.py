from __future__ import annotations

from enclosure.shared import architecture_code, limits

from . import domain


def build_clusters_report() -> domain.ClustersReport:
    return _build_clusters_report(top_override=None, files_top_override=None)


def build_clusters_report_for_limits(
    top: int | None,
    files_top: int | None,
) -> domain.ClustersReport:
    return _build_clusters_report(
        top_override=top,
        files_top_override=files_top,
    )


def _build_clusters_report(
    top_override: int | None,
    files_top_override: int | None,
) -> domain.ClustersReport:
    code_analysis = architecture_code.extract_architecture_code()
    config = code_analysis.config
    top = limits.validate_report_limit(
        config.clusters.top if top_override is None else top_override
    )
    files_top = limits.validate_report_limit(
        config.clusters.files_top
        if files_top_override is None
        else files_top_override
    )
    clusters = limits.apply_limit(
        domain.describe_clusters(
            code_analysis.code_map,
            group_depth=config.clusters.group_depth,
        ),
        top,
    )
    return domain.ClustersReport(
        **code_analysis.report_fields(),
        group_depth=config.clusters.group_depth,
        top=top,
        files_top=files_top,
        clusters=clusters,
    )


__all__ = [
    "build_clusters_report",
    "build_clusters_report_for_limits",
]
