from __future__ import annotations

from pathlib import Path

from .config import RulesConfig
from .documents import (
    RuleDocument,
    RuleDocumentCheck,
    RuleDocumentClass,
    RuleDocumentFile,
    RuleDocumentScope,
    RuleSchemaViolation,
)
from .references import RuleReference, resolve_reference_path
from .schema import RuleDocumentSchema, RuleSectionRequirement


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
        return resolve_reference_path(reference)


__all__ = ["RuleSchemaPolicy"]
