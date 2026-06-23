from __future__ import annotations

from importlib import import_module
from pathlib import Path

_documents = import_module("enclosure.features.workspace.rules.domain.documents")
_graph = import_module("enclosure.features.workspace.rules.domain.graph")
_metadata = import_module("enclosure.features.workspace.rules.domain.metadata")
_policy = import_module("enclosure.features.workspace.rules.domain.policy")

RuleDocumentCheck = _documents.RuleDocumentCheck
RuleDocumentFile = _documents.RuleDocumentFile
RuleDocumentParseError = _metadata.RuleDocumentParseError
RuleReadPlan = _graph.RuleReadPlan
RuleReadStep = _graph.RuleReadStep
RuleSchemaReport = _documents.RuleSchemaReport
RuleSchemaPolicy = _policy.RuleSchemaPolicy
RuleSchemaViolation = _documents.RuleSchemaViolation


def build_rule_schema_report() -> RuleSchemaReport:
    application = import_module("enclosure.features.workspace.rules.application")
    return application.build_rule_schema_report()


def build_rule_read_plan(
    tags: tuple[str, ...],
    *,
    paths: tuple[Path, ...] = (),
    task: str = "",
) -> RuleReadPlan:
    application = import_module("enclosure.features.workspace.rules.application")
    return application.build_rule_read_plan(tags, paths=paths, task=task)


__all__ = [
    "RuleDocumentCheck",
    "RuleDocumentFile",
    "RuleDocumentParseError",
    "RuleReadPlan",
    "RuleReadStep",
    "RuleSchemaReport",
    "RuleSchemaPolicy",
    "RuleSchemaViolation",
    "build_rule_read_plan",
    "build_rule_schema_report",
]
