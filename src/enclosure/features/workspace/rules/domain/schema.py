from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .documents import RuleDocumentClass


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


__all__ = [
    "RuleDocumentSchema",
    "RuleSectionRequirement",
]
