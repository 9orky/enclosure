from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path, PurePosixPath
from posixpath import normpath
from typing import Literal, Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

from enclosure.shared import config

_FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\n(?P<value>.*?)\n---\s*(?:\n|\Z)",
    re.DOTALL,
)
_SECTION_HEADING_PATTERN = re.compile(r"^##\s+(?P<value>.+)$", re.MULTILINE)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)]+)\)")


class RuleDocumentParseError(ValueError):
    pass


class LocalRulesConfig(config.StrictConfigModel):
    max_content_chars: int = 2400

    @field_validator("max_content_chars")
    @classmethod
    def validate_max_content_chars(cls, value: int) -> int:
        if value < -1:
            raise ValueError("Local rule content threshold must be -1 or greater")
        return value


class RulesConfig(config.StrictConfigModel):
    local: LocalRulesConfig = Field(default_factory=LocalRulesConfig)


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


class RuleSectionRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    headings: tuple[str, ...]
    required: bool = True

    @field_validator("headings")
    @classmethod
    def validate_headings(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(heading.strip() for heading in values if heading.strip())
        if not normalized:
            raise ValueError(
                "Rule section requirements must declare at least one heading"
            )
        return normalized

    @property
    def canonical_heading(self) -> str:
        return self.headings[0]

    def matches(self, heading: str) -> bool:
        return heading.strip() in self.headings


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


class RuleReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_path: Path
    raw_path: str


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
        return len(_body_content_from(self.content))

    @property
    def is_local(self) -> bool:
        return _document_path_scope(self.path) is RuleDocumentScope.LOCAL


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
    stage: Literal["big_picture", "step"]
    same_artifact_family: str


_RuleDocumentMetadata = (
    NavigationalRuleDocumentMetadata
    | PolicyRuleDocumentMetadata
    | ExecutionRuleDocumentMetadata
)
_RULE_DOCUMENT_METADATA_ADAPTER = TypeAdapter(_RuleDocumentMetadata)


class RuleDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    document_class: RuleDocumentClass
    scope: RuleDocumentScope
    stage: str = ""
    observed_section_headings: tuple[str, ...]
    has_navigation_targets: bool
    content_char_count: int
    references: tuple[RuleReference, ...] = ()

    @classmethod
    def from_file(cls, document_file: RuleDocumentFile) -> RuleDocument:
        metadata = _metadata_from(document_file.content)
        return cls(
            path=document_file.path,
            document_class=RuleDocumentClass.from_literal(metadata.doc_class),
            scope=RuleDocumentScope.from_literal(metadata.scope),
            stage=getattr(metadata, "stage", ""),
            observed_section_headings=_section_headings_from(document_file.content),
            has_navigation_targets=_has_navigation_targets(
                document_file.content,
                metadata,
            ),
            content_char_count=document_file.content_char_count,
            references=_references_from(
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
    collection_complete: bool
    has_findings: bool


class RuleDocumentSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_class: RuleDocumentClass
    section_requirements: tuple[RuleSectionRequirement, ...]
    navigation_targets_required: bool = False

    @model_validator(mode="after")
    def validate_section_requirements(self) -> Self:
        if not self.section_requirements:
            raise ValueError(
                "Rule document schemas must declare at least one section requirement"
            )
        return self

    @classmethod
    def navigational(cls) -> RuleDocumentSchema:
        return cls(
            document_class=RuleDocumentClass.NAVIGATIONAL,
            section_requirements=(
                RuleSectionRequirement(
                    headings=("Use This Branch When",),
                    required=False,
                ),
                RuleSectionRequirement(headings=("Stop Or Descend",)),
                RuleSectionRequirement(headings=("Branches",), required=False),
                RuleSectionRequirement(headings=("Review Checks",)),
            ),
            navigation_targets_required=True,
        )

    @classmethod
    def policy(cls) -> RuleDocumentSchema:
        return cls(
            document_class=RuleDocumentClass.POLICY,
            section_requirements=(
                RuleSectionRequirement(headings=("Required Decisions",)),
                RuleSectionRequirement(headings=("Core Rules",)),
                RuleSectionRequirement(
                    headings=("Layer Starter Rules",),
                    required=False,
                ),
                RuleSectionRequirement(headings=("Review Checks",)),
            ),
        )

    @classmethod
    def local_policy(cls) -> RuleDocumentSchema:
        return cls(
            document_class=RuleDocumentClass.POLICY,
            section_requirements=(
                RuleSectionRequirement(headings=("Rules",)),
                RuleSectionRequirement(headings=("Checks",)),
            ),
        )

    @classmethod
    def execution_big_picture(cls) -> RuleDocumentSchema:
        return cls(
            document_class=RuleDocumentClass.EXECUTION,
            section_requirements=(
                RuleSectionRequirement(headings=("Required Sections",)),
                RuleSectionRequirement(headings=("Optional Sections",), required=False),
                RuleSectionRequirement(headings=("File Tree Rules",)),
                RuleSectionRequirement(headings=("Phase Rules",)),
                RuleSectionRequirement(
                    headings=("Strategic Model Gate",),
                    required=False,
                ),
                RuleSectionRequirement(headings=("Review Checks",)),
                RuleSectionRequirement(headings=("Handoff Checks",)),
            ),
        )

    @classmethod
    def execution_step(cls) -> RuleDocumentSchema:
        return cls(
            document_class=RuleDocumentClass.EXECUTION,
            section_requirements=(
                RuleSectionRequirement(headings=("Required Sections",)),
                RuleSectionRequirement(headings=("Implementation Tree Rules",)),
                RuleSectionRequirement(headings=("Step Contract Rules",)),
                RuleSectionRequirement(headings=("Execution Rules",)),
                RuleSectionRequirement(headings=("Review Checks",)),
                RuleSectionRequirement(headings=("Handoff Checks",)),
            ),
        )

    @classmethod
    def local_execution(cls) -> RuleDocumentSchema:
        return cls(
            document_class=RuleDocumentClass.EXECUTION,
            section_requirements=(
                RuleSectionRequirement(headings=("Rules",)),
                RuleSectionRequirement(headings=("Checks",)),
            ),
        )

    def required_sections(self) -> tuple[RuleSectionRequirement, ...]:
        return tuple(
            requirement
            for requirement in self.section_requirements
            if requirement.required
        )


class RuleDocumentRepository(ABC):
    @abstractmethod
    def find(self, rules_root: Path) -> tuple[RuleDocumentFile, ...]:
        raise NotImplementedError


class RuleSchemaPolicy:
    def __init__(
        self,
        *,
        navigational_schema: RuleDocumentSchema,
        policy_schema: RuleDocumentSchema,
        local_policy_schema: RuleDocumentSchema,
        execution_big_picture_schema: RuleDocumentSchema,
        execution_step_schema: RuleDocumentSchema,
        local_execution_schema: RuleDocumentSchema,
        local_max_content_chars: int,
    ) -> None:
        self._navigational_schema = navigational_schema
        self._policy_schema = policy_schema
        self._local_policy_schema = local_policy_schema
        self._execution_big_picture_schema = execution_big_picture_schema
        self._execution_step_schema = execution_step_schema
        self._local_execution_schema = local_execution_schema
        self._local_max_content_chars = local_max_content_chars

    @classmethod
    def default(cls) -> RuleSchemaPolicy:
        return cls.from_config(RulesConfig())

    @classmethod
    def from_config(cls, rules_config: RulesConfig) -> RuleSchemaPolicy:
        return cls(
            navigational_schema=RuleDocumentSchema.navigational(),
            policy_schema=RuleDocumentSchema.policy(),
            local_policy_schema=RuleDocumentSchema.local_policy(),
            execution_big_picture_schema=RuleDocumentSchema.execution_big_picture(),
            execution_step_schema=RuleDocumentSchema.execution_step(),
            local_execution_schema=RuleDocumentSchema.local_execution(),
            local_max_content_chars=rules_config.local.max_content_chars,
        )

    def schema_for(
        self,
        document_class: RuleDocumentClass,
        *,
        stage: str | None,
        scope: RuleDocumentScope,
    ) -> RuleDocumentSchema:
        if document_class is RuleDocumentClass.NAVIGATIONAL:
            return self._navigational_schema
        if document_class is RuleDocumentClass.POLICY:
            if scope is RuleDocumentScope.LOCAL:
                return self._local_policy_schema
            return self._policy_schema
        if scope is RuleDocumentScope.LOCAL:
            return self._local_execution_schema
        if stage == "big_picture":
            return self._execution_big_picture_schema
        return self._execution_step_schema

    @property
    def local_max_content_chars(self) -> int:
        return self._local_max_content_chars

    def validate_file(
        self,
        document_file: RuleDocumentFile,
    ) -> tuple[RuleSchemaViolation, ...]:
        if not document_file.is_local or self._local_max_content_chars < 0:
            return ()
        if document_file.content_char_count <= self._local_max_content_chars:
            return ()
        return (
            RuleSchemaViolation(
                code="local-content-too-large",
                message=(
                    "Local rule content is "
                    f"{document_file.content_char_count} characters; "
                    f"configured maximum is {self._local_max_content_chars}"
                ),
            ),
        )

    @staticmethod
    def validate_path_scope(
        *,
        document_file: RuleDocumentFile,
        document: RuleDocument,
    ) -> tuple[RuleSchemaViolation, ...]:
        expected_scope = (
            RuleDocumentScope.LOCAL
            if document_file.is_local
            else RuleDocumentScope.SHARED
        )
        if document.scope is expected_scope:
            return ()
        return (
            RuleSchemaViolation(
                code="invalid-frontmatter-scope",
                message=(
                    f"Rule frontmatter scope is {document.scope}; expected "
                    f"{expected_scope} for this rules path"
                ),
            ),
        )

    def validate_document(
        self,
        *,
        document_class: RuleDocumentClass,
        scope: RuleDocumentScope,
        observed_section_headings: tuple[str, ...],
        has_navigation_targets: bool,
        stage: str | None,
    ) -> tuple[RuleSchemaViolation, ...]:
        schema = self.schema_for(document_class, stage=stage, scope=scope)
        violations = list(
            self._validate_requirements(
                observed_headings=observed_section_headings,
                requirements=schema.section_requirements,
                missing_code="missing-section",
                invalid_order_code="invalid-section-order",
                missing_message_prefix="Missing required section",
                invalid_order_message_prefix="Section order is invalid",
            )
        )

        if schema.navigation_targets_required and not has_navigation_targets:
            violations.append(
                RuleSchemaViolation(
                    code="missing-navigation-targets",
                    message=(
                        "Navigational documents must declare at least one "
                        "navigation target"
                    ),
                )
            )

        return tuple(violations)

    def inspect_document(self, document_file: RuleDocumentFile) -> RuleDocumentCheck:
        document = RuleDocument.from_file(document_file)
        return RuleDocumentCheck(
            document=document,
            violations=(
                self.validate_file(document_file)
                + self.validate_path_scope(
                    document_file=document_file,
                    document=document,
                )
                + self.validate_document(
                    document_class=document.document_class,
                    scope=document.scope,
                    observed_section_headings=document.observed_section_headings,
                    has_navigation_targets=document.has_navigation_targets,
                    stage=document.stage,
                )
            ),
        )

    def validate_references(
        self,
        *,
        document: RuleDocument,
        known_paths: set[Path],
    ) -> tuple[RuleSchemaViolation, ...]:
        violations: list[RuleSchemaViolation] = []

        for reference in document.references:
            resolved_path = self._resolve_reference_path(reference)
            if resolved_path is None:
                violations.append(
                    RuleSchemaViolation(
                        code="invalid-reference-path",
                        message=(
                            "Rule reference must resolve to a markdown rule "
                            "document inside the rules tree"
                        ),
                        reference_path=reference.raw_path,
                    )
                )
                continue

            if resolved_path not in known_paths:
                violations.append(
                    RuleSchemaViolation(
                        code="missing-reference-target",
                        message=(
                            "Rule reference does not point to a discovered "
                            "rule document"
                        ),
                        reference_path=reference.raw_path,
                    )
                )

        return tuple(violations)

    def _validate_requirements(
        self,
        *,
        observed_headings: tuple[str, ...],
        requirements: tuple[RuleSectionRequirement, ...],
        missing_code: str,
        invalid_order_code: str,
        missing_message_prefix: str,
        invalid_order_message_prefix: str,
    ) -> tuple[RuleSchemaViolation, ...]:
        violations: list[RuleSchemaViolation] = []
        positions: list[tuple[int, str]] = []

        for requirement in requirements:
            matched_index = self._find_heading_index(observed_headings, requirement)
            if matched_index is None:
                if requirement.required:
                    violations.append(
                        RuleSchemaViolation(
                            code=missing_code,
                            message=(
                                f"{missing_message_prefix}: "
                                f"{requirement.canonical_heading}"
                            ),
                            section_heading=requirement.canonical_heading,
                        )
                    )
                continue
            positions.append((matched_index, requirement.canonical_heading))

        violations.extend(
            self._ordering_violations(
                section_positions=positions,
                invalid_order_code=invalid_order_code,
                invalid_order_message_prefix=invalid_order_message_prefix,
            )
        )
        return tuple(violations)

    @staticmethod
    def _find_heading_index(
        observed_headings: tuple[str, ...],
        requirement: RuleSectionRequirement,
    ) -> int | None:
        for index, heading in enumerate(observed_headings):
            if requirement.matches(heading):
                return index
        return None

    @staticmethod
    def _ordering_violations(
        *,
        section_positions: list[tuple[int, str]],
        invalid_order_code: str,
        invalid_order_message_prefix: str,
    ) -> tuple[RuleSchemaViolation, ...]:
        violations: list[RuleSchemaViolation] = []

        for current_index in range(1, len(section_positions)):
            previous_position, previous_heading = section_positions[current_index - 1]
            current_position, current_heading = section_positions[current_index]
            if current_position < previous_position:
                violations.append(
                    RuleSchemaViolation(
                        code=invalid_order_code,
                        message=(
                            f"{invalid_order_message_prefix}: {current_heading} "
                            f"appears before {previous_heading}"
                        ),
                        section_heading=current_heading,
                    )
                )

        return tuple(violations)

    @staticmethod
    def _resolve_reference_path(reference: RuleReference) -> Path | None:
        base_path = PurePosixPath(reference.source_path.as_posix()).parent
        normalized_reference = normpath(str(base_path.joinpath(reference.raw_path)))
        resolved_path = PurePosixPath(normalized_reference)

        if str(resolved_path) == ".":
            return None
        if resolved_path.is_absolute():
            return None
        if resolved_path.suffix != ".md":
            return None
        if any(part == ".." for part in resolved_path.parts):
            return None

        return Path(str(resolved_path))


def _metadata_from(content: str) -> _RuleDocumentMetadata:
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


def _section_headings_from(content: str) -> tuple[str, ...]:
    return tuple(
        match.group("value").strip()
        for match in _SECTION_HEADING_PATTERN.finditer(content)
    )


def _has_navigation_targets(
    content: str,
    metadata: _RuleDocumentMetadata,
) -> bool:
    if isinstance(metadata, NavigationalRuleDocumentMetadata) and metadata.child_paths:
        return True
    return _MARKDOWN_LINK_PATTERN.search(content) is not None


def _references_from(
    document_path: Path,
    metadata: _RuleDocumentMetadata,
    content: str,
) -> tuple[RuleReference, ...]:
    if isinstance(metadata, NavigationalRuleDocumentMetadata):
        raw_paths = (
            metadata.child_paths
            + metadata.tightens_paths
            + metadata.escalation_paths
            + _markdown_rule_reference_paths(content)
        )
    else:
        raw_paths = (
            metadata.tightens_paths
            + metadata.escalation_paths
            + _markdown_rule_reference_paths(content)
        )

    return tuple(
        RuleReference(
            source_path=document_path,
            raw_path=_normalize_reference_path(raw_path),
        )
        for raw_path in _unique_reference_paths(raw_paths)
    )


def _normalize_reference_path(raw_path: str) -> str:
    cleaned = raw_path.strip().split("#", 1)[0].split("?", 1)[0]
    normalized = normpath(cleaned)
    return "." if normalized == "" else normalized


def _markdown_rule_reference_paths(content: str) -> tuple[str, ...]:
    references: list[str] = []
    for match in _MARKDOWN_LINK_PATTERN.finditer(content):
        target = match.group("target").strip()
        if _is_external_or_anchor_reference(target):
            continue
        references.append(target)
    return tuple(references)


def _is_external_or_anchor_reference(raw_path: str) -> bool:
    return (
        raw_path.startswith("#")
        or raw_path.startswith("mailto:")
        or "://" in raw_path
    )


def _unique_reference_paths(raw_paths: tuple[str, ...]) -> tuple[str, ...]:
    unique_paths: list[str] = []
    seen: set[str] = set()
    for raw_path in raw_paths:
        normalized_path = _normalize_reference_path(raw_path)
        if normalized_path in seen:
            continue
        seen.add(normalized_path)
        unique_paths.append(raw_path)
    return tuple(unique_paths)


def _body_content_from(content: str) -> str:
    match = _FRONTMATTER_PATTERN.match(content)
    if match is None:
        return content
    return content[match.end():]


def _document_path_scope(path: Path) -> RuleDocumentScope:
    if path.parts and path.parts[0] == RuleDocumentScope.LOCAL.value:
        return RuleDocumentScope.LOCAL
    return RuleDocumentScope.SHARED


__all__ = [
    "LocalRulesConfig",
    "RuleDocument",
    "RuleDocumentCheck",
    "RuleDocumentClass",
    "RuleDocumentFile",
    "RuleDocumentParseError",
    "RuleDocumentReport",
    "RuleDocumentRepository",
    "RuleDocumentScope",
    "RuleSchemaReport",
    "RuleDocumentSchema",
    "RuleSchemaPolicy",
    "RuleSchemaViolation",
    "RuleSchemaViolationReport",
    "RuleSectionRequirement",
    "RulesConfig",
]
