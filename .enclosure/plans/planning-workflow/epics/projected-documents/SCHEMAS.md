# Projected Documents Schemas

## Navigation

- Epic: [Projected Planning Documents](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#projected-planning-documents) -> [PLAN.md](../../PLAN.md#projected-documents) -> [UML.md](../../UML.md#slug-identity-contract)
- Native sources: [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)
- Siblings: [USER_STORIES.md](USER_STORIES.md)

These schemas are implementation contracts shown as a display projection. The
native sources are `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`; during
projection updates their content is pasted into the sections below.

`tree.mermaid` defines the expected files, `uml.mermaid` defines expected
symbols and file ownership, and `flows.mermaid` defines the closed stage loop
that turns input data into derived output slots, projected documents,
eventsourcing aggregate events, and next-stage output data.

Every concrete stage owns the file model for the stage files it projects,
including markdown and native Mermaid files. Projection adapters write declared
stage file models; they do not infer stage-owned files from prose or folder
names.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#dbeafe", "primaryTextColor": "#172033", "primaryBorderColor": "#2563eb", "secondaryColor": "#e0f2fe", "secondaryBorderColor": "#0284c7", "tertiaryColor": "#f8fafc", "lineColor": "#2563eb"}}}%%
flowchart LR
    subgraph commands["Parameterless Commands"]
      cmd_start(["command: workspace plan start"])
      cmd_next(["command: workspace plan next"])
      cmd_agent(["command: workspace plan agent"])
      cmd_roll(["command: workspace plan roll"])
    end

    subgraph application["Application Layer"]
      start_uc["usecase: StartPlan"]
      advance_uc["usecase: AdvanceStage"]
      agent_uc["usecase: PrepareAgentContext"]
      roll_uc["usecase: RollProjections"]
      app["PlanningApplication\nextends eventsourcing.application.Application"]
      projection_port["port: ProjectionStore"]
      stage_catalog_port["port: StageCatalog"]
    end

    subgraph domain["Domain Layer"]
      plan["Plan\nextends eventsourcing.domain.Aggregate"]
      created["Plan.Created\nextends Aggregate.Created"]
      accepted["Plan.StageOutputAccepted\nextends Aggregate.Event"]
      recorded["Plan.ProjectionRecorded\nextends Aggregate.Event"]
      advanced["Plan.StageAdvanced\nextends Aggregate.Event"]
      roll_requested["Plan.RollRequested\nextends Aggregate.Event"]
      trigger["plan.trigger_event(...)\nconstructs event, mutates Plan,\nappends pending event"]
      registry["StageRegistry\nstores PlanningStage instances"]
      stage_contract["PlanningStage\nABC / interface"]
      stage_impl["concrete domain stage\nDraftStage / PlanStage / EpicsStage"]
      stage_methods["derive_slots / scaffold /\nagent_context / parse_review /\nvalidate_review / accept"]
      result["StageResult\naccepted / blocked / needs_update / drift"]
      output["StageOutput\nnext stage + data objects + slots"]
      enrichment["Enrichment\nkeyed by derived slot id"]
    end

    subgraph infrastructure["Infrastructure Layer"]
      projection_adapter["FilesystemProjectionStore"]
      catalog_adapter["FilesystemStageCatalog\nimports stage modules if needed"]
      files["DRAFT.md / PLAN.md / UML.md /\nepics/* / native Mermaid"]
      schemas["SCHEMAS.md\ndisplay projection from native Mermaid"]
    end

    subgraph eventsourcing_boilerplate["eventsourcing Boilerplate"]
      repo["repository.get(plan_id)\nreconstructs Plan from stored events"]
      save["Application.save(plan)\ncollects pending aggregate events"]
      notification_log["notification_log\nordered aggregate events"]
    end

    cmd_start --> start_uc
    cmd_next --> advance_uc
    cmd_agent --> agent_uc
    cmd_roll --> roll_uc

    start_uc --> app
    advance_uc --> app
    agent_uc --> app
    roll_uc --> app
    app --> repo
    repo --> plan
    plan --> created

    stage_catalog_port --> catalog_adapter
    catalog_adapter --> registry
    advance_uc --> registry
    agent_uc --> registry
    roll_uc --> registry
    registry --> stage_contract
    stage_contract --> stage_impl
    stage_impl --> stage_methods

    advance_uc --> stage_methods
    agent_uc --> stage_methods
    roll_uc --> stage_methods
    stage_methods --> result
    result --> output
    output -->|"plan.accept_stage_output(output)"| trigger
    trigger --> accepted
    trigger --> recorded
    trigger --> advanced
    roll_uc -->|"plan.request_roll(reason)"| trigger
    trigger --> roll_requested
    trigger --> save
    save --> notification_log
    notification_log --> repo

    projection_port --> projection_adapter
    advance_uc --> projection_port
    roll_uc --> projection_port
    projection_adapter --> files
    files --> schemas
    output --> enrichment
    result -->|"blocked or drift"| cmd_agent

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef app fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef domain fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef infra fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef event fill:#fee2e2,stroke:#dc2626,color:#172033;
    class cmd_start,cmd_next,cmd_agent,cmd_roll command;
    class start_uc,advance_uc,agent_uc,roll_uc,app,projection_port,stage_catalog_port app;
    class plan,registry,stage_contract,stage_impl,stage_methods,result,output,enrichment domain;
    class projection_adapter,catalog_adapter,files,schemas infra;
    class created,accepted,recorded,advanced,roll_requested,trigger,repo,save,notification_log event;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f5f3ff", "primaryTextColor": "#172033", "primaryBorderColor": "#7c3aed", "secondaryColor": "#ede9fe", "secondaryBorderColor": "#6d28d9", "tertiaryColor": "#faf5ff", "lineColor": "#7c3aed"}}}%%
classDiagram
    class PlanningStage {
      <<ABC: domain/stage.py>>
      +stage_id() str
      +intake_type() type
      +output_type() type
      +file_models(StageInput) List~StageFileModel~
      +derive_slots(StageInput) List~DerivedSlot~
      +scaffold(StageInput) StageProjection
      +agent_context(StageInput) AgentContext
      +parse_review(StageProjection) ReviewData
      +validate_review(ReviewData) ValidationResult
      +accept(ReviewData) StageResult
    }

    class StageSchemaContract {
      <<ABC: domain/stage.py>>
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class DraftStage {
      <<file: domain/stages/draft_stage.py>>
      +stage_id() str
      +intake_type() type
      +output_type() type
      +file_models(StageInput) List~StageFileModel~
      +derive_slots(StageInput) List~DerivedSlot~
      +scaffold(StageInput) StageProjection
      +agent_context(StageInput) AgentContext
      +parse_review(StageProjection) ReviewData
      +validate_review(ReviewData) ValidationResult
      +accept(ReviewData) StageResult
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class PlanStage {
      <<file: domain/stages/plan_stage.py>>
      +stage_id() str
      +intake_type() type
      +output_type() type
      +file_models(StageInput) List~StageFileModel~
      +derive_slots(StageInput) List~DerivedSlot~
      +scaffold(StageInput) StageProjection
      +agent_context(StageInput) AgentContext
      +parse_review(StageProjection) ReviewData
      +validate_review(ReviewData) ValidationResult
      +accept(ReviewData) StageResult
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class EpicsStage {
      <<file: domain/stages/epics_stage.py>>
      +stage_id() str
      +intake_type() type
      +output_type() type
      +file_models(StageInput) List~StageFileModel~
      +derive_slots(StageInput) List~DerivedSlot~
      +scaffold(StageInput) StageProjection
      +agent_context(StageInput) AgentContext
      +parse_review(StageProjection) ReviewData
      +validate_review(ReviewData) ValidationResult
      +accept(ReviewData) StageResult
      +schema_file_models(StageInput) List~StageFileModel~
      +render_schema_display(StageInput, NativeSchemas) ProjectedArtifact
    }

    class StageRegistry {
      <<file: domain/stage_registry.py>>
      +__init__(List~PlanningStage~) None
      +default() StageRegistry
      +current_for(Plan) PlanningStage
      +next_after(PlanningStage) PlanningStage
      +register(PlanningStage) None
    }

    class StageInput {
      <<file: domain/stage_data.py>>
      +str stage_id
      +List~StageData~ data_objects
    }

    class StageFileModel {
      <<file: domain/stage_data.py>>
      +str path
      +str artifact_kind
      +str model_kind
      +bool native_schema_source
    }

    class StageData {
      <<file: domain/stage_data.py>>
      +str id
      +str stable_identity
      +dict~str_to_Any~ values
    }

    class DerivedSlot {
      <<file: domain/stage_data.py>>
      +str id
      +str upstream_identity
      +str stage_id
      +str variant_key
    }

    class StageOutput {
      <<file: domain/stage_data.py>>
      +str stage_id
      +str next_stage_id
      +List~StageData~ data_objects
      +List~DerivedSlot~ derived_slots
    }

    class ProjectedArtifact {
      <<file: domain/stage_data.py>>
      +str path
      +str content
      +str artifact_kind
    }

    class StageProjection {
      <<file: domain/stage_data.py>>
      +str stage_id
      +List~ProjectedArtifact~ artifacts
    }

    class AgentContext {
      <<file: domain/stage_data.py>>
      +str stage_id
      +List~StageFileModel~ file_models
    }

    class ReviewData {
      <<file: domain/stage_data.py>>
      +str stage_id
      +dict~str_to_Any~ values
    }

    class ValidationResult {
      <<file: domain/stage_data.py>>
      +bool valid
      +List~str~ messages
    }

    class DriftReport {
      <<file: domain/stage_data.py>>
      +List~str~ messages
    }

    class StageResult {
      <<file: domain/stage_data.py>>
      +str status
      +StageOutput output
      +List~ProjectedArtifact~ artifacts
      +List~OpenQuestion~ questions
      +DriftReport drift
    }

    class NativeSchemas {
      <<file: domain/stage_data.py>>
      +str flows_mermaid
      +str uml_mermaid
      +str tree_mermaid
    }

    class Enrichment {
      <<file: domain/enrichment.py>>
      +str slot_id
      +dict~str_to_Any~ values
    }

    class ProjectionStore {
      <<Protocol: domain/ports/projection_store.py>>
      +read_text(str) str
      +write_projection(ProjectedArtifact) ProjectionRecord
      +content_hash(str) str
    }

    class StageCatalog {
      <<Protocol: domain/ports/stage_catalog.py>>
      +load_stages() List~PlanningStage~
    }

    class FilesystemProjectionStore {
      <<Adapter: infrastructure/projection_store.py>>
      +Path root
      +read_text(str) str
      +write_projection(ProjectedArtifact) ProjectionRecord
      +content_hash(str) str
    }

    class FilesystemStageCatalog {
      <<Adapter: infrastructure/stage_catalog.py>>
      +load_stages() List~PlanningStage~
    }

    class Plan {
      <<Aggregate: domain/plan.py>>
      +str current_stage
    }

    class ProjectionRecord {
      <<Value Object: domain/plan.py>>
      +str id
      +str path
      +str stage
    }

    PlanningStage <|-- DraftStage
    PlanningStage <|-- PlanStage
    PlanningStage <|-- EpicsStage
    StageSchemaContract <|-- DraftStage
    StageSchemaContract <|-- PlanStage
    StageSchemaContract <|-- EpicsStage
    ProjectionStore <|.. FilesystemProjectionStore
    StageCatalog <|.. FilesystemStageCatalog
    StageRegistry "1" --> "1..*" PlanningStage : stores domain stages
    StageRegistry "1" --> "1" Plan : selects current stage
    PlanningStage "1" --> "1..*" StageFileModel : owns stage file modeling
    PlanningStage "1" --> "0..*" DerivedSlot : derives slots
    PlanningStage "1" --> "1" StageProjection : scaffolds
    StageInput "1" --> "0..*" StageData : carries
    StageOutput "1" --> "0..*" StageData : emits
    StageOutput "1" --> "0..*" DerivedSlot : emits
    StageProjection "1" --> "0..*" ProjectedArtifact : contains
    StageResult "1" --> "1" StageOutput : returns
    StageResult "1" --> "0..*" ProjectedArtifact : returns
    StageResult "1" --> "1" DriftReport : reports
    StageSchemaContract "1" --> "0..*" StageFileModel : owns schema sources
    StageSchemaContract "1" --> "1" NativeSchemas : reads native Mermaid
    StageSchemaContract "1" --> "1" ProjectedArtifact : renders SCHEMAS.md
    FilesystemProjectionStore "1" --> "1" ProjectedArtifact : writes
    FilesystemProjectionStore "1" --> "1" ProjectionRecord : records
    FilesystemStageCatalog "1" --> "1..*" PlanningStage : loads stages
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#ecfdf5", "primaryTextColor": "#064e3b", "primaryBorderColor": "#059669", "labelColor": "#064e3b", "lineColor": "#059669", "tertiaryColor": "#f0fdf4"}}}%%
treeView-beta
  "features/workspace/plan"
    "__init__.py"
    "domain"
      "__init__.py"
      "plan.py"
      "events.py"
      "questions.py"
      "stage.py"
      "stage_data.py"
      "enrichment.py"
      "stage_registry.py"
      "ports"
        "__init__.py"
        "projection_store.py"
        "stage_catalog.py"
      "stages"
        "__init__.py"
        "draft_stage.py"
        "plan_stage.py"
        "epics_stage.py"
    "application.py"
    "infrastructure"
      "__init__.py"
      "persistence.py"
      "projection_store.py"
      "stage_catalog.py"
    "workspace.py"
    "ui"
      "__init__.py"
      "cli.py"
      "templates"
        "current.tmpl"
        "started.tmpl"
        "docs.tmpl"
        "llm.tmpl"
```
