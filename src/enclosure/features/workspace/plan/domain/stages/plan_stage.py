from __future__ import annotations

from .. import stage, stage_data


class PlanStage(stage.PlanningStage, stage.StageSchemaContract):
    def stage_id(self) -> str:
        return "plan"

    def intake_type(self) -> type:
        return stage_data.StageInput

    def output_type(self) -> type:
        return stage_data.StageOutput

    def file_models(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.StageFileModel]:
        return [
            stage_data.StageFileModel(
                path="PLAN.md",
                artifact_kind="markdown",
                model_kind="plan_contract",
                native_schema_source=False,
            ),
            stage_data.StageFileModel(
                path="UML.md",
                artifact_kind="markdown",
                model_kind="technical_view",
                native_schema_source=False,
            ),
        ]

    def schema_file_models(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.StageFileModel]:
        return []

    def render_schema_display(
        self,
        stage_input: stage_data.StageInput,
        native_schemas: stage_data.NativeSchemas,
    ) -> stage_data.ProjectedArtifact:
        raise ValueError("PlanStage does not own a schema display projection")

    def derive_slots(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.DerivedSlot]:
        return [
            stage_data.DerivedSlot(
                id=f"{data_object.stable_identity}:{self.stage_id()}",
                upstream_identity=data_object.stable_identity,
                stage_id=self.stage_id(),
                variant_key=self.stage_id(),
            )
            for data_object in stage_input.data_objects
        ]

    def scaffold(
        self,
        stage_input: stage_data.StageInput,
    ) -> stage_data.StageProjection:
        return stage_data.StageProjection(
            stage_id=self.stage_id(),
            artifacts=[
                stage_data.ProjectedArtifact(
                    path=file_model.path,
                    content="",
                    artifact_kind=file_model.artifact_kind,
                )
                for file_model in self.file_models(stage_input)
            ],
        )

    def agent_context(
        self,
        stage_input: stage_data.StageInput,
    ) -> stage_data.AgentContext:
        return stage_data.AgentContext(
            stage_id=self.stage_id(),
            file_models=self.file_models(stage_input),
        )

    def parse_review(
        self,
        projection: stage_data.StageProjection,
    ) -> stage_data.ReviewData:
        return stage_data.ReviewData(stage_id=projection.stage_id, values={})

    def validate_review(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.ValidationResult:
        return stage_data.ValidationResult(valid=True, messages=[])

    def accept(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.StageResult:
        return stage_data.StageResult(
            status="accepted",
            output=stage_data.StageOutput(
                stage_id=self.stage_id(),
                next_stage_id="epics",
                data_objects=[],
                derived_slots=[],
            ),
            artifacts=[],
            questions=[],
            drift=stage_data.DriftReport(messages=[]),
        )


__all__ = ["PlanStage"]
