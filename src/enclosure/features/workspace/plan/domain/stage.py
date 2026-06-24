from __future__ import annotations

from abc import ABC, abstractmethod

from . import stage_data


class PlanningStage(ABC):
    @abstractmethod
    def stage_id(self) -> str:
        ...

    @abstractmethod
    def intake_type(self) -> type:
        ...

    @abstractmethod
    def output_type(self) -> type:
        ...


class StageFileContract(ABC):
    @abstractmethod
    def file_models(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.StageFileModel]:
        ...

    @abstractmethod
    def derive_slots(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.DerivedSlot]:
        ...

    @abstractmethod
    def scaffold(
        self,
        stage_input: stage_data.StageInput,
    ) -> stage_data.StageProjection:
        ...

    @abstractmethod
    def agent_context(
        self,
        stage_input: stage_data.StageInput,
    ) -> stage_data.AgentContext:
        ...

    @abstractmethod
    def parse_review(
        self,
        projection: stage_data.StageProjection,
    ) -> stage_data.ReviewData:
        ...

    @abstractmethod
    def validate_review(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.ValidationResult:
        ...

    @abstractmethod
    def accept(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.StageResult:
        ...


class StageSchemaContract(ABC):
    @abstractmethod
    def schema_file_models(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.StageFileModel]:
        ...

    @abstractmethod
    def render_schema_display(
        self,
        stage_input: stage_data.StageInput,
        native_schemas: stage_data.NativeSchemas,
    ) -> stage_data.ProjectedArtifact:
        ...


__all__ = [
    "StageFileContract",
    "PlanningStage",
    "StageSchemaContract",
]
