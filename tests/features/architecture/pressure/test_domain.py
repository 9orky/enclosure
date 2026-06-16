from __future__ import annotations

from modwire import CodeMap
from modwire.definitions import (
    SourceCall,
    SourceCallable,
    SourceExport,
    SourceFile,
    SourceImport,
)
from modwire.extraction import ExtractionResult, ExtractionSummary
from modwire.graph import DependencyGraph

from enclosure.features.architecture.pressure import domain


def test_describe_architecture_pressure_ranks_callables_and_exports() -> None:
    report = domain.describe_architecture_pressure(_code_map(), top=2)

    assert report.callable_count == 4
    assert report.call_count == 5
    assert report.resolved_call_count == 4
    assert report.unresolved_call_count == 1
    assert report.unresolved_call_breakdown.internal_candidate_count == 0
    assert report.unresolved_call_breakdown.unknown_count == 1
    assert [pressure.qualified_name for pressure in report.most_calling] == [
        "orchestrate",
        "target",
    ]
    assert [pressure.qualified_name for pressure in report.most_called] == [
        "target",
        "other",
    ]
    assert [pressure.qualified_name for pressure in report.wide_signatures] == [
        "orchestrate",
        "helper",
    ]
    assert [pressure.source_id for pressure in report.reexport_hubs] == [
        "feature/api/__init__"
    ]
    assert report.reexport_hubs[0].reexported_count == 2
    assert report.reexport_hubs[0].source_modules == (
        "feature/api/application",
        "feature/api/domain",
    )


def test_describe_architecture_pressure_honors_zero_limit() -> None:
    report = domain.describe_architecture_pressure(_code_map(), top=0)

    assert report.most_calling == ()
    assert report.most_called == ()
    assert report.wide_signatures == ()
    assert report.reexport_hubs == ()
    assert report.public_api_hubs == ()


def test_unresolved_call_breakdown_splits_internal_candidates_from_context() -> None:
    report = domain.describe_architecture_pressure(
        _code_map(include_unresolved_breakdown=True),
        top=2,
    )

    assert report.unresolved_call_count == 6
    assert report.unresolved_call_breakdown.internal_candidate_count == 2
    assert report.unresolved_call_breakdown.builtin_count == 1
    assert report.unresolved_call_breakdown.external_import_count == 1
    assert report.unresolved_call_breakdown.attribute_or_dynamic_count == 1
    assert report.unresolved_call_breakdown.unknown_count == 1
    assert report.unresolved_call_breakdown.non_actionable_count == 4


def test_pressure_locations_do_not_invent_python_extensions() -> None:
    report = domain.describe_architecture_pressure(_code_map(), top=2)

    assert report.most_calling[0].location == "feature/api/application:10"
    assert report.reexport_hubs[0].location == "feature/api/__init__"


def test_reexport_hubs_are_not_limited_to_python_init_modules() -> None:
    report = domain.describe_architecture_pressure(
        _code_map(public_source_id="feature/api/index"),
        top=2,
    )

    assert [pressure.source_id for pressure in report.reexport_hubs] == [
        "feature/api/index"
    ]


def _code_map(
    public_source_id: str = "feature/api/__init__",
    *,
    include_unresolved_breakdown: bool = False,
) -> CodeMap:
    application_imports = []
    application_calls = [
        _call(
            "feature/api/application::orchestrate",
            "feature/api/domain::target",
            line=12,
            target_name="target",
        ),
        _call(
            "feature/api/application::orchestrate",
            "feature/api/domain::target",
            line=13,
            target_name="target",
        ),
        _call(
            "feature/api/application::orchestrate",
            "feature/api/domain::other",
            line=14,
            target_name="other",
        ),
        SourceCall(
            source_callable_id="feature/api/application::orchestrate",
            target_callable_id="",
            source_id="feature/api/application",
            line=15,
            expression="external()",
            resolution="unresolved",
            target_name="external",
        ),
    ]
    if include_unresolved_breakdown:
        application_imports = [
            _import("domain", "feature/api/domain", is_relative=True),
            _import("Path", "pathlib"),
        ]
        application_calls.extend(
            [
                SourceCall(
                    source_callable_id="feature/api/application::orchestrate",
                    target_callable_id="",
                    source_id="feature/api/application",
                    line=16,
                    expression="domain.Target()",
                    resolution="unresolved",
                    target_name="domain.Target",
                ),
                SourceCall(
                    source_callable_id="feature/api/application::orchestrate",
                    target_callable_id="",
                    source_id="feature/api/application",
                    line=17,
                    expression="other()",
                    resolution="unresolved",
                    target_name="other",
                ),
                SourceCall(
                    source_callable_id="feature/api/application::orchestrate",
                    target_callable_id="",
                    source_id="feature/api/application",
                    line=18,
                    expression="len(items)",
                    resolution="unresolved",
                    target_name="len",
                ),
                SourceCall(
                    source_callable_id="feature/api/application::orchestrate",
                    target_callable_id="",
                    source_id="feature/api/application",
                    line=19,
                    expression="Path(value)",
                    resolution="unresolved",
                    target_name="Path",
                ),
                SourceCall(
                    source_callable_id="feature/api/application::orchestrate",
                    target_callable_id="",
                    source_id="feature/api/application",
                    line=20,
                    expression="items.append(value)",
                    resolution="unresolved",
                    target_name="items.append",
                ),
            ]
        )
    files = {
        public_source_id: SourceFile(
            imports=[],
            exports=[
                SourceExport(
                    name="ApiReport",
                    local_name="ApiReport",
                    kind="class",
                    crossing_type="symbol",
                    path="feature/api/domain",
                    is_relative=True,
                    normalized_path="feature/api/domain",
                    is_reexport=True,
                    is_default=False,
                    is_aliased=False,
                    statement_id=1,
                ),
                SourceExport(
                    name="build_report",
                    local_name="build_report",
                    kind="function",
                    crossing_type="symbol",
                    path="feature/api/application",
                    is_relative=True,
                    normalized_path="feature/api/application",
                    is_reexport=True,
                    is_default=False,
                    is_aliased=False,
                    statement_id=2,
                ),
            ],
            classes=[],
            functions=[],
            callables=[],
            calls=[],
            line_count=3,
            code_line_count=2,
            public_symbol_count=2,
        ),
        "feature/api/application": SourceFile(
            imports=application_imports,
            exports=[],
            classes=[],
            functions=[],
            callables=[
                _callable("feature/api/application", "orchestrate", 10, 4),
                _callable("feature/api/application", "helper", 30, 3),
            ],
            calls=application_calls,
            line_count=40,
            code_line_count=30,
            public_symbol_count=2,
        ),
        "feature/api/domain": SourceFile(
            imports=[],
            exports=[],
            classes=[],
            functions=[],
            callables=[
                _callable("feature/api/domain", "target", 5, 1),
                _callable("feature/api/domain", "other", 15, 1),
            ],
            calls=[
                _call(
                    "feature/api/domain::target",
                    "feature/api/domain::other",
                    line=7,
                    target_name="other",
                ),
            ],
            line_count=20,
            code_line_count=16,
            public_symbol_count=2,
        ),
    }
    graph = DependencyGraph()
    for source_id in files:
        graph.add_node(source_id)
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
        runtime_command="test",
    )


def _callable(
    source_id: str,
    qualified_name: str,
    line_start: int,
    declared_args: int,
) -> SourceCallable:
    return SourceCallable(
        id=f"{source_id}::{qualified_name}",
        source_id=source_id,
        name=qualified_name,
        qualified_name=qualified_name,
        kind="function",
        visibility="public",
        visibility_intent="public",
        line_start=line_start,
        line_end=line_start + 1,
        line_count=2,
        declared_args=declared_args,
        optional_args=0,
    )


def _call(
    source_callable_id: str,
    target_callable_id: str,
    *,
    line: int,
    target_name: str,
) -> SourceCall:
    return SourceCall(
        source_callable_id=source_callable_id,
        target_callable_id=target_callable_id,
        source_id=source_callable_id.split("::", maxsplit=1)[0],
        line=line,
        expression=f"{target_name}()",
        resolution="resolved",
        target_name=target_name,
    )


def _import(
    imported_name: str,
    normalized_path: str,
    *,
    is_relative: bool = False,
) -> SourceImport:
    return SourceImport(
        path=normalized_path.replace("/", "."),
        is_relative=is_relative,
        normalized_path=normalized_path,
        imported_name=imported_name,
        is_aliased=False,
        crossing_type="module",
        file_barrier_crossed=False,
        statement_id=1,
        join_key="",
        uses_joined_import=False,
    )
