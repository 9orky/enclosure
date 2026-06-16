from __future__ import annotations

from modwire.architecture import ArchitecturePolicyEvaluator

import enclosure.features.architecture.clusters
import enclosure.features.architecture.coherence
import enclosure.features.architecture.map
import enclosure.features.architecture.pressure
import enclosure.features.architecture.shape
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
    boundary_violations = tuple(
        ArchitecturePolicyEvaluator().evaluate(
            code_map.tracked_only().graph,
            code_analysis.matching_config,
        )
    )
    shape_violations = enclosure.features.architecture.shape.evaluate_shape(
        code_map,
        config,
    )
    mapped = enclosure.features.architecture.map.describe_architecture_map(
        code_map.graph,
        code_analysis.matching_config,
        tracked_files=tuple(code_map.extraction_result.files),
        top=config.map.top,
    )
    all_clusters = enclosure.features.architecture.clusters.describe_clusters(
        code_map,
        group_depth=config.clusters.group_depth,
    )
    clusters = limits.apply_limit(all_clusters, top)
    pressure = enclosure.features.architecture.pressure.describe_architecture_pressure(
        code_map,
        top=top,
    )
    coherence = enclosure.features.architecture.coherence.describe_coherence(
        code_map,
        code_analysis.matching_config,
        top,
    )

    return domain.ArchitectureHealthReport(
        **report_fields,
        boundary_violation_count=len(boundary_violations),
        shape_violation_count=len(shape_violations),
        unknown_file_count=len(mapped.unknown_files),
        module_count=len(mapped.modules),
        cross_module_dependency_count=len(mapped.dependencies),
        cluster_count=len(all_clusters),
        callable_count=pressure.callable_count,
        call_count=pressure.call_count,
        unresolved_call_count=pressure.unresolved_call_count,
        unresolved_internal_call_count=(
            pressure.unresolved_call_breakdown.internal_candidate_count
        ),
        unresolved_non_actionable_call_count=(
            pressure.unresolved_call_breakdown.non_actionable_count
        ),
        coherence_stream_count=coherence.stream_count,
        coherence_finding_count=coherence.finding_count,
        cluster_group_depth=config.clusters.group_depth,
        cluster_files_top=config.clusters.files_top,
        top=top,
        findings=_findings(
            files_checked=report_fields["files_checked"],
            boundary_violation_count=len(boundary_violations),
            shape_violation_count=len(shape_violations),
            unknown_file_count=len(mapped.unknown_files),
            pressure_clusters=clusters,
            unresolved_internal_call_count=(
                pressure.unresolved_call_breakdown.internal_candidate_count
            ),
            unresolved_non_actionable_call_count=(
                pressure.unresolved_call_breakdown.non_actionable_count
            ),
            coherence_finding_count=coherence.finding_count,
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
            for cluster in limits.apply_limit(clusters, top)
        ),
        boundary_violations=boundary_violations,
        shape_violations=shape_violations,
        modules=mapped.modules,
        dependencies=mapped.dependencies,
        unknown_files=mapped.unknown_files,
        clusters=clusters,
        most_calling=pressure.most_calling,
        most_called=pressure.most_called,
        wide_signatures=pressure.wide_signatures,
        reexport_hubs=pressure.reexport_hubs,
        public_api_hubs=pressure.public_api_hubs,
        coherence_streams=coherence.streams,
        coherence_findings=coherence.findings,
    )


def _findings(
    *,
    files_checked: int,
    boundary_violation_count: int,
    shape_violation_count: int,
    unknown_file_count: int,
    pressure_clusters: tuple[
        enclosure.features.architecture.clusters.ArchitectureCluster,
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
                detail=f"{unknown_file_count} file(s) outside configured module tags.",
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
