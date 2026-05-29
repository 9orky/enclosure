from __future__ import annotations

from importlib import import_module
from pathlib import Path

from . import domain

RuleDocumentCheck = domain.RuleDocumentCheck
RuleDocumentFile = domain.RuleDocumentFile
RuleDocumentParseError = domain.RuleDocumentParseError
RuleReadPlan = domain.RuleReadPlan
RuleReadStep = domain.RuleReadStep
RuleSchemaReport = domain.RuleSchemaReport
RuleSchemaPolicy = domain.RuleSchemaPolicy
RuleSchemaViolation = domain.RuleSchemaViolation
RulesConfig = domain.RulesConfig


def build_rule_schema_report() -> domain.RuleSchemaReport:
    application = import_module("enclosure.features.workspace.rules.application")
    return application.build_rule_schema_report()


def build_rule_read_plan(
    tags: tuple[str, ...],
    *,
    paths: tuple[Path, ...] = (),
    task: str = "",
) -> domain.RuleReadPlan:
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
    "RulesConfig",
    "build_rule_read_plan",
    "build_rule_schema_report",
]
