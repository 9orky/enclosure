from __future__ import annotations

from collections import defaultdict

from modwire import CodeMap

from . import models, tree


def findings(
    code_map: CodeMap,
    file_maps: dict[str, models.FileMap],
    stream_files: dict[str, tuple[models.FileMap, ...]],
    layer_indexes: dict[str, int],
) -> tuple[tuple[models.CoherenceFinding, ...], dict[str, set[tuple[str, str]]]]:
    dependency_findings: list[models.CoherenceFinding] = []
    dependency_groups: dict[str, set[tuple[str, str]]] = defaultdict(set)
    streams = set(stream_files)
    for edge in sorted(code_map.graph.edges, key=lambda item: (item.from_id, item.to_id)):
        source = file_maps.get(edge.from_id)
        if source is None:
            continue
        target = tree.target_from_path(edge.to_id, streams, file_maps)
        if target is None:
            continue
        if source.stream == target.stream:
            add_internal_edge_finding(
                dependency_findings,
                source,
                target,
                edge.to_id,
                file_maps,
                layer_indexes,
            )
            continue
        dependency_groups[source.stream].add((source.stream, target.stream))
        dependency_groups[target.stream].add((source.stream, target.stream))
        add_cross_stream_findings(
            dependency_findings,
            source,
            target,
            edge.to_id,
            file_maps,
        )
    dependency_findings.extend(pressure_findings(dependency_groups))
    return tuple(dependency_findings), dependency_groups


def add_internal_edge_finding(
    findings: list[models.CoherenceFinding],
    source: models.FileMap,
    target: models.ImportTarget,
    target_path: str,
    file_maps: dict[str, models.FileMap],
    layer_indexes: dict[str, int],
) -> None:
    target_file = file_maps.get(target.source_id)
    if target_file is None or source.is_api or target_file.is_api:
        return
    if not source.layer or not target_file.layer:
        findings.append(
            models.CoherenceFinding(
                stream=source.stream,
                axis="flow",
                subject=f"{source.source_id} -> {target.source_id}",
                detail="Internal edge involves a node outside configured layers.",
                evidence=f"{source.source_id} -> {target_path}",
                impact=15,
            )
        )
        return
    if layer_indexes[source.layer] > layer_indexes[target_file.layer]:
        findings.append(
            models.CoherenceFinding(
                stream=source.stream,
                axis="flow",
                subject=f"{source.layer} -> {target_file.layer}",
                detail="Internal edge points backward through configured layer flow.",
                evidence=f"{source.source_id} -> {target_path}",
                impact=35,
            )
        )


def add_cross_stream_findings(
    findings: list[models.CoherenceFinding],
    source: models.FileMap,
    target: models.ImportTarget,
    target_path: str,
    file_maps: dict[str, models.FileMap],
) -> None:
    if not target.is_api:
        findings.append(
            models.CoherenceFinding(
                stream=source.stream,
                axis="seam_use",
                subject=f"{source.stream} -> {target.stream}",
                detail="Cross-stream edge bypasses the target API seam.",
                evidence=f"{source.source_id} -> {target_path}",
                impact=30,
            )
        )
    if not any(file.stream == target.stream and file.is_api for file in file_maps.values()):
        findings.append(
            models.CoherenceFinding(
                stream=target.stream,
                axis="seam_use",
                subject=f"{source.stream} -> {target.stream}",
                detail="Incoming edge targets a stream with no API seam node.",
                evidence=f"{source.source_id} -> {target_path}",
                impact=20,
            )
        )


def pressure_findings(
    dependency_groups: dict[str, set[tuple[str, str]]],
) -> tuple[models.CoherenceFinding, ...]:
    pressure: list[models.CoherenceFinding] = []
    for stream, groups in sorted(dependency_groups.items()):
        if not groups:
            continue
        evidence = ", ".join(f"{source} -> {target}" for source, target in sorted(groups))
        group_count = len(groups)
        pressure.append(
            models.CoherenceFinding(
                stream=stream,
                axis="dependency_pressure",
                subject="cross-stream dependencies",
                detail=f"{group_count} cross-stream dependency group(s) involve stream.",
                evidence=evidence,
                impact=min(group_count * 10, 60),
            )
        )
    return tuple(pressure)


__all__ = ["findings"]
