from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .violations import FlowViolation


@dataclass(frozen=True)
class FlowAnalyzer:
    name: str
    title: str
    run: Callable


def supported_analyzers() -> tuple[str, ...]:
    return tuple(_ANALYZERS)


def analyzer_title(name: str) -> str:
    return _ANALYZERS[name].title


def run_analyzer(name: str, graph, tags, config):
    analyzer = _ANALYZERS[name]
    return analyzer.run(analyzer.name, graph, tags, config)


def _roots(graph):
    incoming = {node_id: 0 for node_id in graph.node_ids()}
    for edge in graph.edges:
        if edge.to_id in incoming:
            incoming[edge.to_id] += 1
    roots = [node_id for node_id, count in incoming.items() if count == 0]
    return tuple(sorted(roots or incoming))


def _dedupe(violations):
    seen = set()
    unique = []
    for violation in violations:
        key = (violation.violation_type, violation.path, violation.violation_index)
        if key not in seen:
            seen.add(key)
            unique.append(violation)
    return unique


def _flow(name, path, index, message):
    return FlowViolation(name, tuple(path), index, f"analyzer:{name}", message)


def _backward_flow(name, graph, tags, config):
    layers = config.rules.flow.layers

    def layer(node):
        return next((i for i, layer_name in enumerate(layers) if layer_name in tags.get(node, set())), None)

    violations = []
    seen = set()

    def walk(node, current_layer, path):
        if (node, current_layer) in seen:
            return
        seen.add((node, current_layer))
        for edge in graph.outgoing(node):
            next_layer = layer(edge.to_id)
            if current_layer is not None and next_layer is not None and next_layer < current_layer:
                violations.append(_flow(name, [*path, edge.to_id], len(path), "layer order violated"))
                continue
            walk(edge.to_id, current_layer if next_layer is None else next_layer, [*path, edge.to_id])

    for root in _roots(graph):
        walk(root, layer(root), [root])
    return _dedupe(violations)


def _no_reentry(name, graph, tags, config):
    module_tag = config.rules.flow.module_tag
    violations = []
    seen = set()

    def walk(node, state, path):
        if (node, state) in seen:
            return
        seen.add((node, state))
        for edge in graph.outgoing(node):
            inside = module_tag in tags.get(edge.to_id, set())
            next_state = 1 if state == 0 and inside else 2 if state == 1 and not inside else state
            if state == 2 and inside:
                violations.append(_flow(name, [*path, edge.to_id], len(path), "module layer re-entered after exit"))
                continue
            walk(edge.to_id, next_state, [*path, edge.to_id])

    for root in _roots(graph):
        walk(root, 1 if module_tag in tags.get(root, set()) else 0, [root])
    return _dedupe(violations)


def _no_cycles(name, graph, tags, config):
    scoped = {node for node, node_tags in tags.items() if config.rules.flow.module_tag in node_tags}
    seen, stack, index, emitted, violations = set(), [], {}, set(), []

    def canonical(cycle):
        ring = list(cycle[:-1])
        first = min(tuple(ring[i:] + ring[:i]) for i in range(len(ring)))
        return (*first, first[0])

    def dfs(node):
        seen.add(node)
        index[node] = len(stack)
        stack.append(node)
        for edge in graph.outgoing(node):
            if edge.to_id not in scoped:
                continue
            if edge.to_id in index:
                cycle = tuple([*stack[index[edge.to_id] :], edge.to_id])
                key = canonical(cycle)
                if key not in emitted:
                    emitted.add(key)
                    violations.append(_flow(name, cycle, len(cycle) - 1, "module cycle detected"))
            elif edge.to_id not in seen:
                dfs(edge.to_id)
        stack.pop()
        index.pop(node, None)

    for node in sorted(scoped):
        if node not in seen:
            dfs(node)
    return violations


_ANALYZERS = {
    analyzer.name: analyzer
    for analyzer in (
        FlowAnalyzer("backward-flow", "Backward Flow Violations", _backward_flow),
        FlowAnalyzer("no-reentry", "No Re-Entry Violations", _no_reentry),
        FlowAnalyzer("no-cycles", "Cycle Violations", _no_cycles),
    )
}
