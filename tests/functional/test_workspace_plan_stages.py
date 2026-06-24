from __future__ import annotations

from pathlib import Path

from enclosure.features.workspace.plan import domain
from enclosure.features.workspace.plan import infrastructure


def test_each_planning_stage_declares_file_models() -> None:
    stages = [
        domain.DraftStage(),
        domain.PlanStage(),
        domain.EpicsStage(),
    ]

    for stage in stages:
        file_models = stage.file_models(
            domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
        )

        assert file_models
        assert all(file_model.path for file_model in file_models)
        assert all(file_model.artifact_kind for file_model in file_models)
        assert all(file_model.model_kind for file_model in file_models)


def test_epics_stage_owns_native_mermaid_schema_sources() -> None:
    stage = domain.EpicsStage()

    native_sources = [
        file_model.path
        for file_model in stage.schema_file_models(
            domain.StageInput(stage_id="epics", data_objects=[])
        )
    ]

    assert native_sources == [
        "epics/{epic_id}/flows.mermaid",
        "epics/{epic_id}/uml.mermaid",
        "epics/{epic_id}/tree.mermaid",
    ]


def test_stage_registry_uses_stage_ids_without_switching_on_types() -> None:
    registry = domain.StageRegistry(
        stages=[
            domain.DraftStage(),
            domain.PlanStage(),
            domain.EpicsStage(),
        ]
    )

    next_stage = registry.next_after(domain.DraftStage())

    assert next_stage.stage_id() == "plan"


def test_stages_implement_stage_schema_contract() -> None:
    stages = [
        domain.DraftStage(),
        domain.PlanStage(),
        domain.EpicsStage(),
    ]

    assert all(isinstance(stage, domain.StageSchemaContract) for stage in stages)


def test_stages_implement_stage_file_contract() -> None:
    stages = [
        domain.DraftStage(),
        domain.PlanStage(),
        domain.EpicsStage(),
    ]

    assert all(isinstance(stage, domain.StageFileContract) for stage in stages)


def test_epics_stage_pastes_native_mermaid_sources_into_schema_display() -> None:
    stage = domain.EpicsStage()

    artifact = stage.render_schema_display(
        domain.StageInput(stage_id="epics", data_objects=[]),
        domain.NativeSchemas(
            flows_mermaid="flowchart LR\nA --> B\n",
            uml_mermaid="classDiagram\nclass A\n",
            tree_mermaid='treeView-beta\n  "root"\n',
        )
    )

    assert artifact.path == "epics/{epic_id}/SCHEMAS.md"
    assert artifact.artifact_kind == "markdown"
    assert "## Flow\n\n```mermaid\nflowchart LR\nA --> B\n```" in artifact.content
    assert "## UML\n\n```mermaid\nclassDiagram\nclass A\n```" in artifact.content
    assert '## Tree\n\n```mermaid\ntreeView-beta\n  "root"\n```' in artifact.content


def test_filesystem_projection_store_writes_projection(tmp_path: Path) -> None:
    store = infrastructure.FilesystemProjectionStore(root=tmp_path)
    artifact = domain.ProjectedArtifact(
        path="plans/SCHEMAS.md",
        content="# Schemas\n",
        artifact_kind="markdown",
    )

    record = store.write_projection(artifact)

    assert (tmp_path / "plans" / "SCHEMAS.md").read_text(encoding="utf-8") == "# Schemas\n"
    assert record.path == "plans/SCHEMAS.md"
    assert record.id == store.content_hash("# Schemas\n")


def test_filesystem_stage_catalog_loads_concrete_stage_order() -> None:
    catalog = infrastructure.FilesystemStageCatalog()

    stage_ids = [stage.stage_id() for stage in catalog.load_stages()]

    assert stage_ids == ["draft", "plan", "epics"]


def test_projection_and_stage_catalog_ports_are_domain_owned() -> None:
    assert domain.ProjectionStore.__module__.endswith("domain.ports.projection_store")
    assert domain.StageCatalog.__module__.endswith("domain.ports.stage_catalog")
