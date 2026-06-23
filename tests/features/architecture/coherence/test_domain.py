from __future__ import annotations

from types import SimpleNamespace

from modwire import CodeMap
from modwire.definitions import SourceFile
from modwire.extraction import ExtractionResult, ExtractionSummary
from modwire.graph import DependencyGraph

from enclosure.features.architecture.coherence import domain
from enclosure.shared.config.architecture import ConfigTagRule

LAYERS = ("ui", "application", "infrastructure", "domain")


def test_coherent_abstract_stream_has_full_axis_scores() -> None:
    report = domain.describe_coherence(
        code_map(
            (
                "sales/orders/api",
                "sales/orders/domain",
                "sales/orders/application",
                "sales/orders/ui/cli",
            ),
            (
                ("sales/orders/application", "sales/orders/domain"),
                ("sales/orders/ui/cli", "sales/orders/application"),
            ),
        ),
        architecture_config(),
        -1,
    )

    assert report.finding_count == 0
    assert report.stream_count == 1
    assert report.streams[0].name == "sales/orders"
    assert axis_scores(report.streams[0]) == {
        "naming": 100,
        "tree_shape": 100,
        "sibling_pattern": 100,
        "flow": 100,
        "seam_use": 100,
        "dependency_pressure": 100,
    }


def test_incoherent_abstract_stream_reports_each_axis() -> None:
    report = domain.describe_coherence(
        code_map(
            (
                "sales/BadStream/api",
                "sales/BadStream/domain",
                "sales/BadStream/domain/model",
                "sales/BadStream/application",
                "sales/BadStream/toolbox",
                "sales/Other/domain",
            ),
            (
                ("sales/BadStream/domain", "sales/BadStream/application"),
                ("sales/BadStream/application", "sales/BadStream/toolbox"),
                ("sales/BadStream/toolbox", "package/sales/Other/domain"),
            ),
        ),
        architecture_config(),
        -1,
    )

    findings = {(finding.stream, finding.axis, finding.subject) for finding in report.findings}
    assert ("sales/BadStream", "naming", "BadStream") in findings
    assert ("sales/BadStream", "tree_shape", "domain") in findings
    assert ("sales/BadStream", "tree_shape", "toolbox") in findings
    assert ("sales/BadStream", "flow", "domain -> application") in findings
    assert (
        "sales/BadStream",
        "flow",
        "sales/BadStream/application -> sales/BadStream/toolbox",
    ) in findings
    assert ("sales/BadStream", "seam_use", "sales/BadStream -> sales/Other") in findings
    assert ("sales/Other", "tree_shape", "public seam") in findings
    assert ("sales/Other", "seam_use", "sales/BadStream -> sales/Other") in findings

    bad_stream = stream_by_name(report, "sales/BadStream")
    assert axis_scores(bad_stream) == {
        "naming": 85,
        "tree_shape": 75,
        "sibling_pattern": 100,
        "flow": 50,
        "seam_use": 70,
        "dependency_pressure": 90,
    }


def test_sibling_pattern_reports_streams_that_break_group_shape() -> None:
    report = domain.describe_coherence(
        code_map(
            (
                "sales/orders/api",
                "sales/orders/domain",
                "sales/orders/application",
                "sales/orders/ui/cli",
                "sales/invoices/api",
                "sales/invoices/domain",
                "sales/invoices/application",
                "sales/invoices/ui/cli",
                "sales/config/api",
                "sales/config/domain",
                "sales/config/infrastructure",
            ),
        ),
        architecture_config(),
        -1,
    )

    findings = {(finding.stream, finding.axis, finding.subject) for finding in report.findings}
    assert ("sales/config", "sibling_pattern", "sales") in findings
    assert axis_scores(stream_by_name(report, "sales/config"))["sibling_pattern"] == 80


def test_missing_module_tag_reports_configuration_finding() -> None:
    report = domain.describe_coherence(
        code_map(("sales/orders/api",)),
        architecture_config(include_module_tag=False),
        -1,
    )

    assert report.stream_count == 0
    assert report.finding_count == 1
    assert report.findings[0].axis == "configuration"
    assert report.findings[0].subject == "module tag"


def architecture_config(
    *,
    include_module_tag: bool = True,
) -> SimpleNamespace:
    tags = []
    if include_module_tag:
        tags.append(
            ConfigTagRule(name="module", match="*/*", **{"except": []}, exclude=[])
        )
    tags.append(
        ConfigTagRule(
            name="module_api",
            match="*/*/api",
            **{"except": []},
            exclude=[],
        )
    )
    tags.extend(
        ConfigTagRule(
            name=layer,
            match=f"*/*/{layer}",
            **{"except": []},
            exclude=[],
        )
        for layer in LAYERS
    )
    return SimpleNamespace(
        architecture_root="",
        language="python",
        rules=SimpleNamespace(
            tags=tags,
            flow=SimpleNamespace(layers=list(LAYERS)),
        ),
    )


def code_map(
    source_ids: tuple[str, ...],
    edges: tuple[tuple[str, str], ...] = (),
) -> CodeMap:
    files = {
        source_id: SourceFile(
            imports=[],
            classes=[],
            functions=[],
            line_count=1,
            code_line_count=1,
            public_symbol_count=0,
        )
        for source_id in source_ids
    }
    graph = DependencyGraph()
    for source_id in source_ids:
        graph.add_node(source_id)
    for source, target in edges:
        graph.add_node(target)
        graph.add_edge(source, target, kind="import")
    return CodeMap(
        graph=graph,
        extraction_result=ExtractionResult(
            files=files,
            summary=ExtractionSummary(
                files_found=len(files),
                files_checked=len(files),
                files_excluded=0,
            ),
        ),
        runtime_command="",
    )


def stream_by_name(
    report: domain.DescribedCoherence,
    name: str,
) -> domain.CoherenceStream:
    return next(stream for stream in report.streams if stream.name == name)


def axis_scores(stream: domain.CoherenceStream) -> dict[str, int]:
    return {score.axis: score.score for score in stream.axis_scores}
