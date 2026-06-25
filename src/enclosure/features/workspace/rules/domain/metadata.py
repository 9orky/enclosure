from __future__ import annotations

import re
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

_FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\n(?P<value>.*?)\n---\s*(?:\n|\Z)",
    re.DOTALL,
)


class RuleDocumentParseError(ValueError):
    pass


class RuleDocumentMetadataBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: Literal["shared", "local"] = "shared"
    audience: str
    purpose: str
    applies_when: tuple[str, ...]
    tags: tuple[str, ...]
    read_directly: bool
    generated_by: str = ""
    validation_version: int = 0
    profile_kind: str = ""
    discovered_from: tuple[str, ...] = ()
    narrows_paths: tuple[str, ...] = ()
    tightens_paths: tuple[str, ...] = ()
    escalation_paths: tuple[str, ...] = ()


class NavigationalRuleDocumentMetadata(RuleDocumentMetadataBase):
    doc_class: Literal["navigational"]
    rule_kind: Literal["navigation"]
    entrypoint: bool
    read_strategy: str
    child_paths: tuple[str, ...]


class PolicyRuleDocumentMetadata(RuleDocumentMetadataBase):
    doc_class: Literal["policy"]
    rule_kind: Literal["policy"]


class ExecutionRuleDocumentMetadata(RuleDocumentMetadataBase):
    doc_class: Literal["execution"]
    rule_kind: Literal["execution"]
    stage: Literal["big_picture", "calibration", "step"]
    same_artifact_family: str


class RuleRuleDocumentMetadata(RuleDocumentMetadataBase):
    doc_class: Literal["rule"]
    rule_kind: str
    read_strategy: str = ""


RuleDocumentMetadata = (
    NavigationalRuleDocumentMetadata
    | PolicyRuleDocumentMetadata
    | ExecutionRuleDocumentMetadata
    | RuleRuleDocumentMetadata
)
_RULE_DOCUMENT_METADATA_ADAPTER = TypeAdapter(RuleDocumentMetadata)


def metadata_from(content: str) -> RuleDocumentMetadata:
    match = _FRONTMATTER_PATTERN.match(content)
    if match is None:
        raise RuleDocumentParseError("Rule document must declare YAML frontmatter")

    payload = yaml.safe_load(match.group("value"))
    if not isinstance(payload, dict):
        raise RuleDocumentParseError("Rule document frontmatter must be a mapping")

    try:
        return _RULE_DOCUMENT_METADATA_ADAPTER.validate_python(payload)
    except ValidationError as exc:
        first_error = exc.errors()[0]["msg"]
        raise RuleDocumentParseError(
            f"Invalid rule document frontmatter: {first_error}"
        ) from exc


def body_content_from(content: str) -> str:
    match = _FRONTMATTER_PATTERN.match(content)
    if match is None:
        return content
    return content[match.end():]


__all__ = [
    "ExecutionRuleDocumentMetadata",
    "NavigationalRuleDocumentMetadata",
    "PolicyRuleDocumentMetadata",
    "RuleRuleDocumentMetadata",
    "RuleDocumentMetadata",
    "RuleDocumentMetadataBase",
    "RuleDocumentParseError",
    "body_content_from",
    "metadata_from",
]
