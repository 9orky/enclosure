from __future__ import annotations

from enclosure.features.architecture.boundaries import application as boundaries
from enclosure.features.architecture.clusters import application as clusters
from enclosure.features.architecture.coherence import application as coherence
from enclosure.features.architecture.health import application as health
from enclosure.features.architecture.map import application as architecture_map
from enclosure.features.architecture.pressure import application as pressure
from enclosure.features.architecture.shape import application as shape


def test_architecture_reports_share_scan_and_health_counts() -> None:
    health_report = health.build_health_report_for_top(-1)
    boundaries_report = boundaries.build_boundaries_report()
    shape_report = shape.build_shape_report()
    map_report = architecture_map.build_map_report_for_top(-1)
    clusters_report = clusters.build_clusters_report_for_limits(-1, -1)
    pressure_report = pressure.build_pressure_report_for_top(-1)
    coherence_report = coherence.build_coherence_report_for_top(-1)

    scan = _scan_tuple(health_report)
    assert _scan_tuple(boundaries_report) == scan
    assert _scan_tuple(shape_report) == scan
    assert _scan_tuple(map_report) == scan
    assert _scan_tuple(clusters_report) == scan
    assert _scan_tuple(pressure_report) == scan
    assert _scan_tuple(coherence_report) == scan

    assert not boundaries_report.violations
    assert health_report.boundary_violation_count == len(boundaries_report.violations)
    assert tuple(health_report.boundary_violations) == boundaries_report.violations
    assert health_report.shape_violation_count == len(shape_report.violations)
    assert tuple(health_report.shape_violations) == shape_report.violations
    assert health_report.module_count == len(map_report.modules)
    assert tuple(health_report.modules) == map_report.modules
    assert health_report.cross_module_dependency_count == len(map_report.dependencies)
    assert tuple(health_report.dependencies) == map_report.dependencies
    assert health_report.unknown_file_count == len(map_report.unknown_files)
    assert health_report.unknown_files == map_report.unknown_files
    assert health_report.cluster_count == len(clusters_report.clusters)
    assert tuple(health_report.clusters) == clusters_report.clusters
    assert health_report.callable_count == pressure_report.callable_count
    assert health_report.call_count == pressure_report.call_count
    assert health_report.unresolved_call_count == pressure_report.unresolved_call_count
    assert (
        health_report.unresolved_internal_call_count
        == pressure_report.unresolved_call_breakdown.internal_candidate_count
    )
    assert health_report.coherence_stream_count == coherence_report.stream_count
    assert health_report.coherence_finding_count == coherence_report.finding_count
    assert tuple(health_report.coherence_streams) == coherence_report.streams
    assert tuple(health_report.coherence_findings) == coherence_report.findings


def test_architecture_map_and_clusters_cover_every_checked_file(
    configured_module_names: tuple[str, ...],
) -> None:
    map_report = architecture_map.build_map_report_for_top(-1)
    clusters_report = clusters.build_clusters_report_for_limits(-1, -1)

    module_files = sorted(file for module in map_report.modules for file in module.files)
    cluster_files = sorted(
        file.path for cluster in clusters_report.clusters for file in cluster.files
    )

    assert not map_report.unknown_files
    assert module_files == cluster_files
    assert len(module_files) == map_report.files_checked
    assert len(cluster_files) == clusters_report.files_checked
    assert len(module_files) == len(set(module_files))
    assert len(cluster_files) == len(set(cluster_files))
    configured_modules = set(configured_module_names)
    discovered_modules = {module.name for module in map_report.modules}
    assert configured_modules.issubset(discovered_modules)


def _scan_tuple(report: object) -> tuple[int, int, int]:
    return (
        getattr(report, "files_found"),
        getattr(report, "files_excluded"),
        getattr(report, "files_checked"),
    )
