from __future__ import annotations

from collections import defaultdict

from modwire import CodeMap

from enclosure.shared import limits

from . import dependencies, models, naming, siblings, structure, tree


def describe_coherence(
    code_map: CodeMap,
    config: object,
    top: int,
) -> models.DescribedCoherence:
    stream_rule = tree.tag_rule(config, "module")
    if stream_rule is None:
        finding = models.CoherenceFinding(
            stream="",
            axis="configuration",
            subject="module tag",
            detail="No feature-module stream tag configured.",
            evidence="architecture.boundaries.tags",
            impact=0,
        )
        return models.DescribedCoherence(
            stream_count=0,
            finding_count=1,
            streams=(),
            findings=limits.apply_limit((finding,), top),
        )

    api_rule = tree.tag_rule(config, "module_api")
    layer_rules = tree.layer_rules(config)
    layer_indexes = {name: index for index, name in enumerate(layer_rules)}
    file_maps = tree.map_files(code_map, config, stream_rule, api_rule, layer_rules)
    stream_files = tree.stream_files(file_maps)
    all_findings = findings(
        code_map,
        file_maps,
        stream_files,
        api_rule,
        layer_indexes,
    )
    all_streams = streams(stream_files, all_findings)
    visible_streams = tuple(
        limit_stream_findings(stream, top)
        for stream in limits.apply_limit(all_streams, top)
    )
    return models.DescribedCoherence(
        stream_count=len(all_streams),
        finding_count=len(all_findings),
        streams=visible_streams,
        findings=limits.apply_limit(all_findings, top),
    )


def findings(
    code_map: CodeMap,
    file_maps: dict[str, models.FileMap],
    stream_files: dict[str, tuple[models.FileMap, ...]],
    api_rule: object | None,
    layer_indexes: dict[str, int],
) -> tuple[models.CoherenceFinding, ...]:
    found: list[models.CoherenceFinding] = []
    if api_rule is None:
        found.append(
            models.CoherenceFinding(
                stream="",
                axis="configuration",
                subject="module_api tag",
                detail="No module API seam tag configured.",
                evidence="architecture.boundaries.tags",
                impact=0,
            )
        )
    found.extend(naming.findings(stream_files))
    found.extend(structure.findings(stream_files, api_rule is not None))
    found.extend(siblings.findings(stream_files))
    dependency_findings, _ = dependencies.findings(
        code_map,
        file_maps,
        stream_files,
        layer_indexes,
    )
    found.extend(dependency_findings)
    return tuple(
        sorted(
            found,
            key=lambda finding: (
                finding.stream,
                finding.axis,
                finding.subject,
                finding.evidence,
            ),
        )
    )


def streams(
    stream_files: dict[str, tuple[models.FileMap, ...]],
    findings: tuple[models.CoherenceFinding, ...],
) -> tuple[models.CoherenceStream, ...]:
    findings_by_stream: dict[str, list[models.CoherenceFinding]] = defaultdict(list)
    for finding in findings:
        if finding.stream:
            findings_by_stream[finding.stream].append(finding)

    all_streams = tuple(
        models.CoherenceStream(
            name=stream,
            source_count=len(files),
            axis_scores=axis_scores(tuple(findings_by_stream[stream])),
            findings=tuple(findings_by_stream[stream]),
        )
        for stream, files in stream_files.items()
    )
    return tuple(
        sorted(
            all_streams,
            key=lambda stream: (
                stream.lowest_score,
                -stream.finding_count,
                stream.name,
            ),
        )
    )


def axis_scores(
    findings: tuple[models.CoherenceFinding, ...],
) -> tuple[models.CoherenceAxisScore, ...]:
    impacts: dict[models.AxisName, int] = {axis: 0 for axis in models.STREAM_AXES}
    for finding in findings:
        if finding.axis in impacts:
            impacts[finding.axis] += finding.impact
    return tuple(
        models.CoherenceAxisScore(axis=axis, score=max(0, 100 - impacts[axis]))
        for axis in models.STREAM_AXES
    )


def limit_stream_findings(
    stream: models.CoherenceStream,
    top: int,
) -> models.CoherenceStream:
    return models.CoherenceStream(
        name=stream.name,
        source_count=stream.source_count,
        axis_scores=stream.axis_scores,
        findings=limits.apply_limit(stream.findings, top),
    )


__all__ = ["describe_coherence"]
