from __future__ import annotations

from modwire import CodeMap
from modwire.architecture import TagMatcher
from modwire.graph import DependencyGraph

from enclosure.features.architecture import flow
from enclosure.shared import architecture_code

from . import domain


def build_boundaries_report() -> domain.BoundariesReport:
    code_analysis = architecture_code.extract_architecture_code()
    return domain.BoundariesReport(
        **code_analysis.report_fields(),
        violations=evaluate_boundaries(
            code_analysis.code_map,
            code_analysis.matching_config,
        ),
    )


def evaluate_boundaries(
    code_map: CodeMap,
    config: object,
) -> tuple[object, ...]:
    return flow.evaluate_policy(
        _internal_dependency_graph(
            code_map,
            config,
        ),
        config,
    )


def _internal_dependency_graph(
    code_map: CodeMap,
    config: object,
) -> DependencyGraph:
    tracked_ids = set(code_map.source_ids())
    public_target_patterns = _public_target_patterns(config)
    public_seam_patterns = flow.public_seam_patterns(config, "")
    matcher = TagMatcher(config)
    graph = DependencyGraph()
    for source_id in sorted(tracked_ids):
        graph.add_node(source_id)
    for edge in code_map.graph.edges:
        if edge.from_id not in tracked_ids:
            continue
        if _is_same_public_seam_reexport(
            edge.from_id,
            edge.to_id,
            matcher,
            public_seam_patterns,
        ):
            continue
        target_id = _tracked_target_id(
            edge.to_id,
            tracked_ids,
            matcher,
            public_target_patterns,
        )
        if target_id is None:
            continue
        graph.add_edge(edge.from_id, target_id, kind=edge.kind)
    return graph


def _is_same_public_seam_reexport(
    source_id: str,
    target_id: str,
    matcher: TagMatcher,
    public_seam_patterns: tuple[str, ...],
) -> bool:
    for pattern in public_seam_patterns:
        match = matcher.match_pattern(source_id, pattern)
        if match is None:
            continue
        module_path = "/".join(str(value) for value in match.wildcard_values)
        if not module_path:
            continue
        target_path = matcher.display_path(target_id)
        if target_path == module_path or target_path.startswith(f"{module_path}/"):
            return True
    return False


def _tracked_target_id(
    target_id: str,
    tracked_ids: set[str],
    matcher: TagMatcher,
    public_target_patterns: tuple[str, ...],
) -> str | None:
    if target_id in tracked_ids:
        return target_id

    for source_id in sorted(tracked_ids, key=lambda value: (-len(value), value)):
        if _ends_with_path(target_id, source_id):
            return source_id
        if _is_public_target_for_import(
            target_id,
            source_id,
            matcher,
            public_target_patterns,
        ):
            return source_id
    return None


def _is_public_target_for_import(
    target_id: str,
    source_id: str,
    matcher: TagMatcher,
    public_target_patterns: tuple[str, ...],
) -> bool:
    target_parts = _path_parts(target_id)
    for pattern in public_target_patterns:
        match = matcher.match_pattern(source_id, pattern)
        if match is None or not match.wildcard_values:
            continue
        wildcard_parts = tuple(
            part
            for value in match.wildcard_values
            for part in _path_parts(value)
        )
        if not wildcard_parts:
            continue
        if len(target_parts) >= len(wildcard_parts) and (
            target_parts[-len(wildcard_parts) :] == wildcard_parts
        ):
            return True
    return False


def _public_target_patterns(config: object) -> tuple[str, ...]:
    patterns: list[str] = []
    for rule in getattr(getattr(config, "rules", object()), "boundaries", ()):
        patterns.extend(getattr(rule, "allow", ()) or ())
    return tuple(dict.fromkeys(patterns))


def _ends_with_path(value: str, suffix: str) -> bool:
    value_parts = _path_parts(value)
    suffix_parts = _path_parts(suffix)
    return len(value_parts) >= len(suffix_parts) and (
        value_parts[-len(suffix_parts) :] == suffix_parts
    )


def _path_parts(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.split("/") if part)


__all__ = [
    "build_boundaries_report",
    "evaluate_boundaries",
]
