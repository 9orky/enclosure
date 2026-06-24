# Schema Contract Verification Schemas

## Navigation

- Epic: [Schema Contract Verification](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#schema-contract-verification) -> [PLAN.md](../../PLAN.md#schema-contract-verification) -> [UML.md](../../UML.md#slug-identity-contract)
- Native sources: [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)
- Siblings: [USER_STORIES.md](USER_STORIES.md)

These schemas are implementation contracts. `tree.mermaid` defines the
stage-owned schema interface files, `uml.mermaid` defines the
`StageSchemaContract` symbols, and `flows.mermaid` defines how stages declare
native Mermaid sources and render the `SCHEMAS.md` display projection.

Schema ownership belongs to stages. Native Mermaid files remain the SSOT; later
modwire comparison must consume those stage-owned native files.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#dbeafe", "primaryTextColor": "#172033", "primaryBorderColor": "#2563eb", "secondaryColor": "#e0f2fe", "secondaryBorderColor": "#0284c7", "tertiaryColor": "#f8fafc", "lineColor": "#2563eb"}}}%%
flowchart LR
    subgraph stage_lane["Stage-Owned Schema Contract"]
      stage["interface: StageSchemaContract\nfile: domain/stage.py\nclass: StageSchemaContract"]
      sources["model: StageFileModel\nfile: domain/stage_data.py\nnative_schema_source flag"]
      native["model: NativeSchemas\nfile: domain/stage_data.py"]
      display["model: ProjectedArtifact\nSCHEMAS.md display projection"]
    end

    subgraph concrete_stages["Concrete Stage Implementations"]
      draft["stage: DraftStage\nfile: domain/stages/draft_stage.py"]
      plan["stage: PlanStage\nfile: domain/stages/plan_stage.py"]
      epics["stage: EpicsStage\nfile: domain/stages/epics_stage.py"]
    end

    subgraph outputs["Outputs"]
      none["output: no native schema files"]
      native_files["output: flows.mermaid / uml.mermaid / tree.mermaid"]
      schemas_md["output: SCHEMAS.md generated from native Mermaid"]
    end

    draft -. implements .-> stage
    plan -. implements .-> stage
    epics -. implements .-> stage
    stage -->|schema_file_models| sources
    draft -->|returns empty list| none
    plan -->|returns empty list| none
    epics -->|returns native sources| native_files
    native_files -->|read as| native
    epics -->|render_schema_display| display
    display --> schemas_md

    classDef stage fill:#dbeafe,stroke:#2563eb,color:#172033;
    classDef model fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef impl fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class stage stage;
    class sources,native,display model;
    class draft,plan,epics impl;
    class none,native_files,schemas_md output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f5f3ff", "primaryTextColor": "#172033", "primaryBorderColor": "#7c3aed", "secondaryColor": "#ede9fe", "secondaryBorderColor": "#6d28d9", "tertiaryColor": "#faf5ff", "lineColor": "#7c3aed"}}}%%
classDiagram
    class StageSchemaContract {
      <<ABC: domain/stage.py>>
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class StageFileModel {
      <<file: domain/stage_data.py>>
      +str path
      +str artifact_kind
      +str model_kind
      +bool native_schema_source
    }

    class NativeSchemas {
      <<file: domain/stage_data.py>>
      +str flows_mermaid
      +str uml_mermaid
      +str tree_mermaid
    }

    class ProjectedArtifact {
      <<file: domain/stage_data.py>>
      +str path
      +str content
      +str artifact_kind
    }

    class DraftStage {
      <<file: domain/stages/draft_stage.py>>
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class PlanStage {
      <<file: domain/stages/plan_stage.py>>
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class EpicsStage {
      <<file: domain/stages/epics_stage.py>>
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    StageSchemaContract <|-- DraftStage
    StageSchemaContract <|-- PlanStage
    StageSchemaContract <|-- EpicsStage
    StageSchemaContract "1" --> "0..*" StageFileModel : declares native schema sources
    StageSchemaContract "1" --> "1" NativeSchemas : receives native Mermaid
    StageSchemaContract "1" --> "1" ProjectedArtifact : renders display projection
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#ecfdf5", "primaryTextColor": "#064e3b", "primaryBorderColor": "#059669", "labelColor": "#064e3b", "lineColor": "#059669", "tertiaryColor": "#f0fdf4"}}}%%
treeView-beta
  "features/workspace/plan"
    "domain"
      "stage.py"
      "stage_data.py"
      "stages"
        "draft_stage.py"
        "plan_stage.py"
        "epics_stage.py"
```
