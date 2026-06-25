from __future__ import annotations

from .. import stage, stage_data


class EpicsStage(
    stage.PlanningStage,
    stage.StageFileContract,
    stage.StageSchemaContract,
):
    def stage_id(self) -> str:
        return "epics"

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
                path="epics/{epic_id}/EPIC.md",
                artifact_kind="markdown",
                model_kind="epic_package",
                native_schema_source=False,
            ),
            stage_data.StageFileModel(
                path="epics/{epic_id}/USER_STORIES.md",
                artifact_kind="markdown",
                model_kind="user_stories",
                native_schema_source=False,
            ),
            stage_data.StageFileModel(
                path="epics/{epic_id}/SCHEMAS.md",
                artifact_kind="markdown",
                model_kind="schema_display_projection",
                native_schema_source=False,
            ),
            stage_data.StageFileModel(
                path="epics/{epic_id}/flows.mermaid",
                artifact_kind="mermaid",
                model_kind="flow_contract",
                native_schema_source=True,
            ),
            stage_data.StageFileModel(
                path="epics/{epic_id}/uml.mermaid",
                artifact_kind="mermaid",
                model_kind="symbol_contract",
                native_schema_source=True,
            ),
            stage_data.StageFileModel(
                path="epics/{epic_id}/tree.mermaid",
                artifact_kind="mermaid",
                model_kind="file_contract",
                native_schema_source=True,
            ),
            stage_data.StageFileModel(
                path="eventmodeling.mermaid",
                artifact_kind="mermaid",
                model_kind="all_epics_event_model",
                native_schema_source=True,
            ),
        ]

    def schema_file_models(
        self,
        stage_input: stage_data.StageInput,
    ) -> list[stage_data.StageFileModel]:
        return [
            file_model
            for file_model in self.file_models(stage_input)
            if file_model.native_schema_source
        ]

    def render_schema_display(
        self,
        stage_input: stage_data.StageInput,
        native_schemas: stage_data.NativeSchemas,
    ) -> stage_data.ProjectedArtifact:
        epic_id = "{epic_id}"
        if stage_input.data_objects:
            epic_id = stage_input.data_objects[0].stable_identity
        content = "\n".join(
            [
                "# Schemas",
                "",
                "## Flow",
                "",
                "```mermaid",
                native_schemas.flows_mermaid.rstrip(),
                "```",
                "",
                "## UML",
                "",
                "```mermaid",
                native_schemas.uml_mermaid.rstrip(),
                "```",
                "",
                "## Tree",
                "",
                "```mermaid",
                native_schemas.tree_mermaid.rstrip(),
                "```",
                "",
            ]
        )
        return stage_data.ProjectedArtifact(
            path=f"epics/{epic_id}/SCHEMAS.md",
            content=content,
            artifact_kind="markdown",
        )

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
        artifacts: list[stage_data.ProjectedArtifact] = []
        for data_object in stage_input.data_objects:
            epic_id = data_object.stable_identity
            name = str(data_object.values.get("name", epic_id))
            intent = str(data_object.values.get("intent", ""))
            planned_outcome = str(data_object.values.get("planned_outcome", ""))
            constraints = data_object.values.get("accepted_constraints", [])
            notes = data_object.values.get("acceptance_notes", [])
            if not isinstance(constraints, list):
                constraints = []
            if not isinstance(notes, list):
                notes = []
            class_name = "".join(
                part.capitalize() for part in epic_id.replace("-", " ").split()
            ) or "Epic"
            flows = "\n".join(
                [
                    "%% contract: flow",
                    '%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#dbeafe", "primaryTextColor": "#172033", "primaryBorderColor": "#2563eb", "secondaryColor": "#e0f2fe", "secondaryBorderColor": "#0284c7", "tertiaryColor": "#f8fafc", "lineColor": "#2563eb"}}}%%',
                    "flowchart LR",
                    '    start(["input: accepted plan item"])',
                    f'    epic["epic: {name}"]',
                    '    stories["output: user stories"]',
                    '    schemas["output: schema contract"]',
                    "    start --> epic",
                    "    epic --> stories",
                    "    epic --> schemas",
                ]
            )
            uml = "\n".join(
                [
                    "%% contract: symbols",
                    '%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f5f3ff", "primaryTextColor": "#172033", "primaryBorderColor": "#7c3aed", "secondaryColor": "#ede9fe", "secondaryBorderColor": "#6d28d9", "tertiaryColor": "#faf5ff", "lineColor": "#7c3aed"}}}%%',
                    "classDiagram",
                    f"    class {class_name} {{",
                    "      +str id",
                    "      +str name",
                    "    }",
                ]
            )
            tree = "\n".join(
                [
                    "%% contract: files",
                    '%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#ecfdf5", "primaryTextColor": "#064e3b", "primaryBorderColor": "#059669", "labelColor": "#064e3b", "lineColor": "#059669", "tertiaryColor": "#f0fdf4"}}}%%',
                    "treeView-beta",
                    f'  "epics/{epic_id}"',
                    '    "EPIC.md"',
                    '    "USER_STORIES.md"',
                    '    "SCHEMAS.md"',
                    '    "flows.mermaid"',
                    '    "uml.mermaid"',
                    '    "tree.mermaid"',
                ]
            )
            epic_lines = [
                f"# {name}",
                "",
                "## Intent",
                "",
                intent or f"{name} is promoted from the accepted plan.",
                "",
                "## Planned Outcome",
                "",
                planned_outcome or f"{name} is implementation-ready.",
                "",
                "## Constraints",
                "",
            ]
            epic_lines.extend(f"- {constraint}" for constraint in constraints)
            epic_lines.extend(["", "## Contract Role", "", "This epic owns its Mermaid schema files as literal implementation contracts.", ""])
            story_lines = [
                f"# {name} User Stories",
                "",
                f"## {epic_id}",
                "",
                f"As a user, I want {name} so that the planned outcome is visible.",
                "",
                "Acceptance criteria:",
                "",
            ]
            if notes:
                story_lines.extend(f"- {note}" for note in notes)
            else:
                story_lines.append("- The epic keeps its stable plan item identity.")
            native = stage_data.NativeSchemas(
                flows_mermaid=flows,
                uml_mermaid=uml,
                tree_mermaid=tree,
            )
            artifacts.extend(
                [
                    stage_data.ProjectedArtifact(
                        path=f"epics/{epic_id}/EPIC.md",
                        content="\n".join(epic_lines),
                        artifact_kind="markdown",
                    ),
                    stage_data.ProjectedArtifact(
                        path=f"epics/{epic_id}/USER_STORIES.md",
                        content="\n".join(story_lines) + "\n",
                        artifact_kind="markdown",
                    ),
                    stage_data.ProjectedArtifact(
                        path=f"epics/{epic_id}/flows.mermaid",
                        content=flows + "\n",
                        artifact_kind="mermaid",
                    ),
                    stage_data.ProjectedArtifact(
                        path=f"epics/{epic_id}/uml.mermaid",
                        content=uml + "\n",
                        artifact_kind="mermaid",
                    ),
                    stage_data.ProjectedArtifact(
                        path=f"epics/{epic_id}/tree.mermaid",
                        content=tree + "\n",
                        artifact_kind="mermaid",
                    ),
                    self.render_schema_display(
                        stage_data.StageInput(
                            stage_id=self.stage_id(),
                            data_objects=[data_object],
                        ),
                        native,
                    ),
                ]
            )
        artifacts.append(self._render_event_modeling(stage_input.data_objects))
        return stage_data.StageProjection(
            stage_id=self.stage_id(),
            artifacts=artifacts,
        )

    def _render_event_modeling(
        self,
        data_objects: list[stage_data.StageData],
    ) -> stage_data.ProjectedArtifact:
        lines = [
            "eventmodeling",
            "",
        ]
        frame = 10
        for data_object in data_objects:
            epic_id = data_object.stable_identity
            symbol = _symbol_name(epic_id)
            lines.extend(
                [
                    f"tf {frame} ui Plan.{symbol}",
                    f"tf {frame + 1} cmd WorkspacePlan.Accept{symbol} ->> {frame}",
                    f"tf {frame + 2} evt WorkspacePlan.{symbol}Accepted ->> {frame + 1}",
                    f"tf {frame + 3} rmo WorkspacePlan.{symbol}PlanItem ->> {frame + 2}",
                    f"tf {frame + 4} pcr WorkspacePlan.Project{symbol}Epic ->> {frame + 3}",
                    f"tf {frame + 5} cmd WorkspacePlan.Project{symbol}Epic ->> {frame + 4}",
                    f"tf {frame + 6} evt WorkspacePlan.{symbol}EpicProjected ->> {frame + 5}",
                    f"tf {frame + 7} rmo Docs.{symbol}Epic ->> {frame + 6}",
                    f"tf {frame + 8} rmo Docs.{symbol}Stories ->> {frame + 6}",
                    f"tf {frame + 9} rmo Docs.{symbol}Schemas ->> {frame + 6}",
                    "",
                ]
            )
            frame += 20
        if not data_objects:
            lines.append("tf 10 rmo Docs.EmptyPlan")
        return stage_data.ProjectedArtifact(
            path="eventmodeling.mermaid",
            content="\n".join(lines).rstrip() + "\n",
            artifact_kind="mermaid",
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
                next_stage_id="complete",
                data_objects=[],
                derived_slots=[],
            ),
            artifacts=[],
            questions=[],
            drift=stage_data.DriftReport(messages=[]),
        )


def _symbol_name(value: str) -> str:
    return (
        "".join(part.capitalize() for part in value.replace("-", " ").split())
        or "Epic"
    )


__all__ = ["EpicsStage"]
