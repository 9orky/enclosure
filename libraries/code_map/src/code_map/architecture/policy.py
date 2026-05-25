from __future__ import annotations

from code_map.graph import DependencyGraph

from .analyzers import run_analyzer
from .matching import match_node
from .violations import EdgeRuleViolation, FlowViolation


class ArchitecturePolicyEvaluator:
    def evaluate(self, graph: DependencyGraph, config):
        tags = _tags(graph.node_ids(), config)
        violations: list[EdgeRuleViolation | FlowViolation] = _edge_violations(graph, config)
        for analyzer_name in config.rules.flow.analyzers:
            violations.extend(run_analyzer(analyzer_name, graph, tags, config))
        return violations


def _edge_violations(graph, config):
    violations = []
    exclusions = {rule.match: rule.excluded_patterns for rule in config.rules.tags}
    for edge in graph.edges:
        denied: tuple[str, str] | None = None
        for rule in config.rules.boundaries:
            source = match_node(edge.from_id, rule.source, config, exclusions)
            if source is None:
                continue
            for target in rule.disallow:
                target_match = match_node(edge.to_id, target, config, exclusions)
                same_owner = (
                    rule.allow_same_match
                    and source[1]
                    and target_match is not None
                    and target_match[1]
                    and source[0] == target_match[0]
                )
                if target_match is not None and not same_owner:
                    denied = (rule.source, target)
            for target in rule.allow:
                if match_node(edge.to_id, target, config, exclusions, scope=target in exclusions):
                    denied = None
        if denied:
            violations.append(
                EdgeRuleViolation(
                    edge.from_id,
                    edge.to_id,
                    denied[0],
                    denied[1],
                    f"boundary:{denied[0]}->{denied[1]}:deny",
                )
            )
    return violations


def _tags(node_ids, config):
    return {
        node_id: {
            rule.name
            for rule in config.rules.tags
            if match_node(node_id, rule.match, config, {}, exclude=rule.excluded_patterns)
        }
        for node_id in node_ids
    }
