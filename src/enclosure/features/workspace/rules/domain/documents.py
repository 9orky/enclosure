from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from .metadata import (
    RuleDocumentParseError,
    body_content_from,
    metadata_from,
)
from .references import (
    RuleReference,
    all_references_from,
    child_references_from,
    escalation_references_from,
    has_markdown_link,
    markdown_references_from,
    tightens_references_from,
)

_SECTION_HEADING_PATTERN = re.compile(r"^##\s+(?P<value>.+)$", re.MULTILINE)


class RuleDocumentClass(StrEnum):
    NAVIGATIONAL = "navigational"
    POLICY = "policy"
    EXECUTION = "execution"

    @classmethod
    def from_literal(cls, value: str) -> RuleDocumentClass:
        return cls(value.strip().lower())


class RuleDocumentScope(StrEnum):
    SHARED = "shared"
    LOCAL = "local"

    @classmethod
    def from_literal(cls, value: str) -> RuleDocumentScope:
        return cls(value.strip().lower())


class RuleSchemaViolation(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    section_heading: str = ""
    reference_path: str = ""


class RuleSchemaViolationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    section_heading: str = ""
    reference_path: str = ""


class RuleDocumentFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    content: str

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        if self.path.suffix != ".md":
            raise ValueError("Rule document files must be markdown documents")
        if not self.content.strip():
            raise ValueError("Rule document files must not be empty")
        return self

    @property
    def content_char_count(self) -> int:
        return len(body_content_from(self.content))

    @property
    def is_local(self) -> bool:
        return document_path_scope(self.path) is RuleDocumentScope.LOCAL


class RuleDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    document_class: RuleDocumentClass
    scope: RuleDocumentScope
    purpose: str = ""
    applies_when: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    read_directly: bool = False
    entrypoint: bool = False
    read_strategy: str = ""
    stage: str = ""
    observed_section_headings: tuple[str, ...]
    has_navigation_targets: bool
    content_char_count: int
    child_references: tuple[RuleReference, ...] = ()
    tightens_references: tuple[RuleReference, ...] = ()
    escalation_references: tuple[RuleReference, ...] = ()
    markdown_references: tuple[RuleReference, ...] = ()
    references: tuple[RuleReference, ...] = ()

    @classmethod
    def from_file(cls, document_file: RuleDocumentFile) -> RuleDocument:
        metadata = metadata_from(document_file.content)
        return cls(
            path=document_file.path,
            document_class=RuleDocumentClass.from_literal(metadata.doc_class),
            scope=RuleDocumentScope.from_literal(metadata.scope),
            purpose=metadata.purpose,
            applies_when=metadata.applies_when,
            tags=metadata.tags,
            read_directly=metadata.read_directly,
            entrypoint=getattr(metadata, "entrypoint", False),
            read_strategy=getattr(metadata, "read_strategy", ""),
            stage=getattr(metadata, "stage", ""),
            observed_section_headings=section_headings_from(document_file.content),
            has_navigation_targets=has_navigation_targets(
                document_file.content,
                metadata,
            ),
            content_char_count=document_file.content_char_count,
            child_references=child_references_from(document_file.path, metadata),
            tightens_references=tightens_references_from(document_file.path, metadata),
            escalation_references=escalation_references_from(
                document_file.path,
                metadata,
            ),
            markdown_references=markdown_references_from(
                document_file.path,
                document_file.content,
            ),
            references=all_references_from(
                document_file.path,
                metadata,
                document_file.content,
            ),
        )


class RuleDocumentCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    document: RuleDocument
    violations: tuple[RuleSchemaViolation, ...]


class RuleDocumentReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    document_class: RuleDocumentClass | str = ""
    scope: RuleDocumentScope | str = ""
    is_local: bool = False
    observed_section_headings: tuple[str, ...] = ()
    has_navigation_targets: bool = False
    content_char_count: int = 0
    violations: tuple[RuleSchemaViolationReport, ...]
    exception: str = ""


class RuleSchemaReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    documents: tuple[RuleDocumentReport, ...]
    documents_discovered: int
    documents_checked: int
    documents_with_issues: int
    local_documents_checked: int
    local_documents_with_issues: int
    local_max_content_chars: int
    available_route_tags: tuple[str, ...] = ()
    collection_complete: bool
    has_findings: bool


class RuleDocumentRepository(ABC):
    @abstractmethod
    def find(self, rules_root: Path) -> tuple[RuleDocumentFile, ...]:
        raise NotImplementedError


def section_headings_from(content: str) -> tuple[str, ...]:
    return tuple(
        match.group("value").strip()
        for match in _SECTION_HEADING_PATTERN.finditer(content)
    )


def has_navigation_targets(
    content: str,
    metadata: object,
) -> bool:
    if getattr(metadata, "child_paths", ()):
        return True
    return has_markdown_link(content)


def document_path_scope(path: Path) -> RuleDocumentScope:
    if path.parts and path.parts[0] == RuleDocumentScope.LOCAL.value:
        return RuleDocumentScope.LOCAL
    return RuleDocumentScope.SHARED


__all__ = [
    "RuleDocument",
    "RuleDocumentCheck",
    "RuleDocumentClass",
    "RuleDocumentFile",
    "RuleDocumentParseError",
    "RuleDocumentReport",
    "RuleDocumentRepository",
    "RuleDocumentScope",
    "RuleReference",
    "RuleSchemaReport",
    "RuleSchemaViolation",
    "RuleSchemaViolationReport",
    "document_path_scope",
]
