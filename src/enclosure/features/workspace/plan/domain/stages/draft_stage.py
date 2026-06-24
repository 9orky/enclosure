from __future__ import annotations

from .. import stage, stage_data


class DraftStage(
    stage.PlanningStage,
    stage.StageFileContract,
    stage.StageSchemaContract,
):
    def stage_id(self) -> str:
        return "draft"

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
                path="DRAFT.md",
                artifact_kind="markdown",
                model_kind="draft_seed",
                native_schema_source=False,
            )
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
        raise ValueError("DraftStage does not own a schema display projection")

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
        title = "Planning Workflow"
        if stage_input.data_objects:
            title = str(stage_input.data_objects[0].values.get("title", title))
        content = "\n".join(
            [
                f"# {title}",
                "",
                "## Abstract",
                "[comment]: <> (Describe briefly your intentions, goals or expectations)",
                "",
                "Summaries are boring, so no summary for you.",
                "",
                "## Use Cases",
                "[comment]: <> (List your Use Cases)",
                "",
                "### YOUR USE CASE NAME",
                "[comment]: <> (Brief description, one paragraph)",
                "",
                "It does something here but not there.",
                "",
                "#### Constraints",
                "[comment]: <> (List of the constraints, rules, etc.)",
                "",
                "- it stinks",
                "- it brings peace",
                "",
            ]
        )
        return stage_data.StageProjection(
            stage_id=self.stage_id(),
            artifacts=[
                stage_data.ProjectedArtifact(
                    path="DRAFT.md",
                    content=content,
                    artifact_kind="markdown",
                )
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
        content = projection.artifacts[0].content if projection.artifacts else ""
        lines = content.splitlines()
        title = ""
        abstract: list[str] = []
        use_cases: list[dict[str, object]] = []
        active_case: dict[str, object] | None = None
        section = ""
        case_section = "description"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                continue
            if stripped.startswith("## "):
                section = stripped[3:].strip().lower()
                active_case = None
                continue
            if section == "abstract":
                if stripped and not stripped.startswith("[comment]:"):
                    abstract.append(stripped)
                continue
            if section != "use cases":
                continue
            if stripped.startswith("### "):
                name = stripped[4:].strip()
                stable_identity = "-".join(
                    "".join(char.lower() if char.isalnum() else " " for char in name)
                    .split()
                ) or "use-case"
                active_case = {
                    "id": stable_identity,
                    "name": name,
                    "description": [],
                    "constraints": [],
                }
                use_cases.append(active_case)
                case_section = "description"
                continue
            if active_case is None or stripped.startswith("[comment]:"):
                continue
            if stripped.startswith("#### "):
                case_section = stripped[5:].strip().lower()
                continue
            if not stripped:
                continue
            if case_section == "constraints" and stripped.startswith("- "):
                constraints = active_case["constraints"]
                if isinstance(constraints, list):
                    constraints.append(stripped[2:].strip())
                continue
            if case_section == "description":
                description = active_case["description"]
                if isinstance(description, list):
                    description.append(stripped)
        return stage_data.ReviewData(
            stage_id=projection.stage_id,
            values={
                "title": title,
                "abstract": " ".join(abstract),
                "use_cases": use_cases,
            },
        )

    def validate_review(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.ValidationResult:
        if not review.values.get("title"):
            return stage_data.ValidationResult(
                valid=False,
                messages=["DRAFT.md must start with a level-one title."],
            )
        if not review.values.get("use_cases"):
            return stage_data.ValidationResult(
                valid=False,
                messages=["DRAFT.md must contain at least one use case."],
            )
        return stage_data.ValidationResult(valid=True, messages=[])

    def accept(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.StageResult:
        use_cases = review.values.get("use_cases", [])
        data_objects = [
            stage_data.StageData(
                id=str(use_case["id"]),
                stable_identity=str(use_case["id"]),
                values={
                    "title": review.values.get("title", ""),
                    "abstract": review.values.get("abstract", ""),
                    "name": use_case["name"],
                    "description": " ".join(use_case["description"]),
                    "constraints": use_case["constraints"],
                },
            )
            for use_case in use_cases
            if isinstance(use_case, dict)
        ]
        return stage_data.StageResult(
            status="accepted",
            output=stage_data.StageOutput(
                stage_id=self.stage_id(),
                next_stage_id="plan",
                data_objects=data_objects,
                derived_slots=[
                    stage_data.DerivedSlot(
                        id=f"{data_object.stable_identity}:plan",
                        upstream_identity=data_object.stable_identity,
                        stage_id="plan",
                        variant_key="plan",
                    )
                    for data_object in data_objects
                ],
            ),
            artifacts=[],
            questions=[],
            drift=stage_data.DriftReport(messages=[]),
        )


__all__ = ["DraftStage"]
