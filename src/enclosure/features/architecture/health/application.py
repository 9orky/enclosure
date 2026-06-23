from __future__ import annotations

from .. import boundaries, clusters, coherence, map, pressure, shape
from enclosure.shared import architecture_code, limits

from . import domain


def build_health_report() -> domain.ArchitectureHealthReport:
    return _build_health_report(top_override=None)


def build_health_report_for_top(top: int | None) -> domain.ArchitectureHealthReport:
    return _build_health_report(top_override=top)


def _build_health_report(top_override: int | None) -> domain.ArchitectureHealthReport:
    code_analysis = architecture_code.extract_architecture_code()
    report_fields = code_analysis.report_fields()
    config = code_analysis.config
    code_map = code_analysis.code_map
    top = limits.validate_report_limit(
        config.health.top if top_override is None else top_override
    )
    boundary_violations = (
        boundaries.evaluate_boundaries(
            code_map,
            code_analysis.matching_config,
        )
    )
    shape_violations = shape.evaluate_shape(
        code_map,
        config,
    )
    mapped = map.describe_architecture_map(
        code_map.graph,
        code_analysis.matching_config,
        tracked_files=tuple(code_map.extraction_result.files),
        top=config.map.top,
    )
    all_clusters = clusters.describe_clusters(
        code_map,
        group_depth=config.clusters.group_depth,
    )
    visible_clusters = limits.apply_limit(all_clusters, top)
    pressure_report = pressure.describe_architecture_pressure(
        code_map,
        top=top,
    )
    coherence_report = coherence.describe_coherence(
        code_map,
        code_analysis.matching_config,
        top,
        code_analysis.project_root / code_analysis.config.architecture_root,
    )

    return domain.ArchitectureHealthReport(
        **report_fields,
        boundary_violation_count=len(boundary_violations),
        shape_violation_count=len(shape_violations),
        unknown_file_count=len(mapped.unknown_files),
        module_count=len(mapped.modules),
        cross_module_dependency_count=len(mapped.dependencies),
        cluster_count=len(all_clusters),
        callable_count=pressure_report.callable_count,
        call_count=pressure_report.call_count,
        unresolved_call_count=pressure_report.unresolved_call_count,
        unresolved_internal_call_count=(
            pressure_report.unresolved_call_breakdown.internal_candidate_count
        ),
        unresolved_non_actionable_call_count=(
            pressure_report.unresolved_call_breakdown.non_actionable_count
        ),
        coherence_stream_count=coherence_report.stream_count,
        coherence_finding_count=coherence_report.finding_count,
        cluster_group_depth=config.clusters.group_depth,
        cluster_files_top=config.clusters.files_top,
        top=top,
        findings=_findings(
            files_checked=report_fields["files_checked"],
            boundary_violation_count=len(boundary_violations),
            shape_violation_count=len(shape_violations),
            unknown_file_count=len(mapped.unknown_files),
            pressure_clusters=visible_clusters,
            unresolved_internal_call_count=(
                pressure_report.unresolved_call_breakdown.internal_candidate_count
            ),
            unresolved_non_actionable_call_count=(
                pressure_report.unresolved_call_breakdown.non_actionable_count
            ),
            coherence_finding_count=coherence_report.finding_count,
        ),
        hotspots=tuple(
            domain.HealthHotspotSummary(
                kind=hotspot.kind,
                name=hotspot.name,
                detail=hotspot.detail,
                score=hotspot.score,
            )
            for hotspot in limits.apply_limit(mapped.hotspots, top)
        ),
        pressure_clusters=tuple(
            domain.HealthClusterSummary(
                name=cluster.name,
                pressure_score=cluster.pressure_score,
                file_count=cluster.file_count,
                incoming_edges=cluster.incoming_edges,
                outgoing_edges=cluster.outgoing_edges,
            )
            for cluster in limits.apply_limit(visible_clusters, top)
        ),
        boundary_violations=boundary_violations,
        shape_violations=shape_violations,
        modules=mapped.modules,
        dependencies=mapped.dependencies,
        unknown_files=mapped.unknown_files,
        clusters=visible_clusters,
        most_calling=pressure_report.most_calling,
        most_called=pressure_report.most_called,
        wide_signatures=pressure_report.wide_signatures,
        reexport_hubs=pressure_report.reexport_hubs,
        public_api_hubs=pressure_report.public_api_hubs,
        coherence_streams=coherence_report.streams,
        coherence_findings=coherence_report.findings,
    )


def _findings(
    *,
    files_checked: int,
    boundary_violation_count: int,
    shape_violation_count: int,
    unknown_file_count: int,
    pressure_clusters: tuple[
        clusters.ArchitectureCluster,
        ...,
    ],
    unresolved_internal_call_count: int,
    unresolved_non_actionable_call_count: int,
    coherence_finding_count: int,
) -> tuple[domain.HealthFinding, ...]:
    findings: list[domain.HealthFinding] = []
    if files_checked == 0:
        findings.append(
            domain.HealthFinding(
                severity="error",
                category="scan",
                subject="code map",
                detail="No files were checked.",
            )
        )
    if boundary_violation_count:
        findings.append(
            domain.HealthFinding(
                severity="error",
                category="boundaries",
                subject="architecture agreement",
                detail=f"{boundary_violation_count} violation(s) detected.",
            )
        )
    if shape_violation_count:
        findings.append(
            domain.HealthFinding(
                severity="error",
                category="shape",
                subject="architecture shape",
                detail=f"{shape_violation_count} violation(s) detected.",
            )
        )
    if unknown_file_count:
        findings.append(
            domain.HealthFinding(
                severity="attention",
                category="map",
                subject="unmapped files",
                detail=(
                    f"{unknown_file_count} file(s) outside configured module "
                    "tags or realms."
                ),
            )
        )
    if unresolved_internal_call_count:
        findings.append(
            domain.HealthFinding(
                severity="attention",
                category="pressure",
                subject="unresolved internal call candidates",
                detail=(
                    f"{unresolved_internal_call_count} internal candidate call(s) "
                    "could not be resolved"
                    f"; {unresolved_non_actionable_call_count} builtin, external, "
                    "or dynamic call(s) are reported as context only."
                ),
            )
        )
    if coherence_finding_count:
        findings.append(
            domain.HealthFinding(
                severity="attention",
                category="coherence",
                subject="architecture streams",
                detail=f"{coherence_finding_count} coherence finding(s) detected.",
            )
        )
    if pressure_clusters:
        cluster = pressure_clusters[0]
        findings.append(
            domain.HealthFinding(
                severity="attention",
                category="clusters",
                subject=cluster.name,
                detail=f"Highest pressure score is {cluster.pressure_score}.",
            )
        )
    return tuple(findings)


__all__ = [
    "build_health_report",
    "build_health_report_for_top",
]
