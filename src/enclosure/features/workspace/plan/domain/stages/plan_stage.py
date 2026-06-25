from __future__ import annotations

from .. import stage, stage_data


class PlanStage(
    stage.PlanningStage,
    stage.StageFileContract,
    stage.StageSchemaContract,
):
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
        title = "Stage Workflow"
        if stage_input.data_objects:
            title = str(stage_input.data_objects[0].values.get("title", title))
        plan_lines = [
            f"# {title}",
            "",
            "## Purpose",
            "",
            "This plan turns the draft use cases into a reviewable implementation contract.",
            "",
            "## Value",
            "",
            "This matters because users get one visible path from intent to implementation-ready work.",
            "",
            "## Use Cases",
            "",
        ]
        uml_lines = [
            f"# {title} UML",
            "",
            "```mermaid",
            "classDiagram",
        ]
        for data_object in stage_input.data_objects:
            plan_item_id = data_object.stable_identity
            name = str(data_object.values.get("name", plan_item_id))
            description = str(data_object.values.get("description", ""))
            constraints = data_object.values.get("constraints", [])
            if not isinstance(constraints, list):
                constraints = []
            plan_lines.extend(
                [
                    f"### {plan_item_id}",
                    "",
                    "#### Name",
                    "",
                    name,
                    "",
                    "#### Intent",
                    "",
                    description
                    or f"The user wants {name} to become implementation-ready.",
                    "",
                    "#### Accepted Constraints",
                    "",
                ]
            )
            plan_lines.extend(f"- {constraint}" for constraint in constraints)
            plan_lines.extend(
                [
                    "",
                    "#### Planned Outcome",
                    "",
                    f"The workflow records {name} as a stable plan item.",
                    "",
                    "#### Acceptance Notes",
                    "",
                    "- The plan item keeps its stable identity.",
                    "- Its constraints remain attached to the item.",
                    "",
                ]
            )
            class_name = "".join(
                part.capitalize() for part in plan_item_id.replace("-", " ").split()
            ) or "PlanItem"
            uml_lines.extend(
                [
                    f"    class {class_name} {{",
                    "      +str id",
                    "      +str name",
                    "    }",
                ]
            )
        plan_lines.extend(
            [
                "## Plan Decisions",
                "",
                "### decision-use-cases-become-plan-items",
                "",
                "#### Decision",
                "",
                "Each draft use case becomes one stable plan item.",
                "",
                "#### Rationale",
                "",
                "Use case headings are the most natural user-authored boundary in the draft.",
                "",
            ]
        )
        uml_lines.extend(["```", ""])
        return stage_data.StageProjection(
            stage_id=self.stage_id(),
            artifacts=[
                stage_data.ProjectedArtifact(
                    path="PLAN.md",
                    content="\n".join(plan_lines),
                    artifact_kind="markdown",
                ),
                stage_data.ProjectedArtifact(
                    path="UML.md",
                    content="\n".join(uml_lines),
                    artifact_kind="markdown",
                ),
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
        content = ""
        for artifact in projection.artifacts:
            if artifact.path == "PLAN.md":
                content = artifact.content
        lines = content.splitlines()
        title = ""
        plan_items: list[dict[str, object]] = []
        decisions: list[str] = []
        active_item: dict[str, object] | None = None
        section = ""
        item_section = ""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                continue
            if stripped.startswith("## "):
                section = stripped[3:].strip().lower()
                active_item = None
                continue
            if section == "plan decisions" and stripped.startswith("### "):
                decisions.append(stripped[4:].strip())
                continue
            if section != "use cases":
                continue
            if stripped.startswith("### "):
                plan_item_id = stripped[4:].strip()
                active_item = {
                    "id": plan_item_id,
                    "name": plan_item_id,
                    "intent": [],
                    "accepted_constraints": [],
                    "planned_outcome": [],
                    "acceptance_notes": [],
                }
                plan_items.append(active_item)
                continue
            if active_item is None:
                continue
            if stripped.startswith("#### "):
                item_section = stripped[5:].strip().lower()
                continue
            if not stripped or stripped.startswith("[comment]:"):
                continue
            if item_section == "name":
                active_item["name"] = stripped
                continue
            if item_section == "accepted constraints" and stripped.startswith("- "):
                accepted_constraints = active_item["accepted_constraints"]
                if isinstance(accepted_constraints, list):
                    accepted_constraints.append(stripped[2:].strip())
                continue
            if item_section == "acceptance notes" and stripped.startswith("- "):
                acceptance_notes = active_item["acceptance_notes"]
                if isinstance(acceptance_notes, list):
                    acceptance_notes.append(stripped[2:].strip())
                continue
            if item_section in {"intent", "planned outcome"}:
                key = item_section.replace(" ", "_")
                values = active_item[key]
                if isinstance(values, list):
                    values.append(stripped)
        return stage_data.ReviewData(
            stage_id=projection.stage_id,
            values={
                "title": title,
                "plan_items": plan_items,
                "decisions": decisions,
            },
        )

    def validate_review(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.ValidationResult:
        if not review.values.get("plan_items"):
            return stage_data.ValidationResult(
                valid=False,
                messages=["PLAN.md must contain at least one plan item."],
            )
        return stage_data.ValidationResult(valid=True, messages=[])

    def accept(
        self,
        review: stage_data.ReviewData,
    ) -> stage_data.StageResult:
        plan_items = review.values.get("plan_items", [])
        data_objects = [
            stage_data.StageData(
                id=str(plan_item["id"]),
                stable_identity=str(plan_item["id"]),
                values={
                    "title": review.values.get("title", ""),
                    "name": plan_item["name"],
                    "intent": " ".join(plan_item["intent"]),
                    "accepted_constraints": plan_item["accepted_constraints"],
                    "planned_outcome": " ".join(plan_item["planned_outcome"]),
                    "acceptance_notes": plan_item["acceptance_notes"],
                },
            )
            for plan_item in plan_items
            if isinstance(plan_item, dict)
        ]
        return stage_data.StageResult(
            status="accepted",
            output=stage_data.StageOutput(
                stage_id=self.stage_id(),
                next_stage_id="epics",
                data_objects=data_objects,
                derived_slots=[
                    stage_data.DerivedSlot(
                        id=f"{data_object.stable_identity}:epics",
                        upstream_identity=data_object.stable_identity,
                        stage_id="epics",
                        variant_key="epic",
                    )
                    for data_object in data_objects
                ],
            ),
            artifacts=[],
            questions=[],
            drift=stage_data.DriftReport(messages=[]),
        )


__all__ = ["PlanStage"]
