from __future__ import annotations

from dataclasses import dataclass


EDGE_RULE_TYPE = "edge-rule"


@dataclass(frozen=True)
class EdgeRuleViolation:
    source_id: str
    target_id: str
    source_pattern: str
    target_pattern: str
    rule_name: str


@dataclass(frozen=True)
class FlowViolation:
    violation_type: str
    path: tuple[str, ...]
    violation_index: int
    rule_name: str
    message: str
