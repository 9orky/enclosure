# Projected Documents Schemas

These schemas are implementation contracts shown as a display projection. The
native sources are `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`; during
projection updates their content is pasted into the sections below.

`tree.mermaid` defines the expected files, `uml.mermaid` defines expected
symbols and file ownership, and `flows.mermaid` defines the closed stage loop
that turns input data into derived output slots, projected documents, and
next-stage output data.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Parameterless Commands"]
      cmd_start(["command: workspace plan start"])
      cmd_next(["command: workspace plan next"])
      cmd_agent(["command: workspace plan agent"])
      cmd_roll(["command: workspace plan roll"])
    end

    subgraph loop["Closed Stage Loop"]
      active["current stage\nselected from event state"]
      intake["input data objects\nfrom prior stage or DRAFT seed"]
      slots["derived output slots\ninput id + stage id + variant key"]
      scaffold["stage scaffold\nproject docs for review"]
      agent_update["agent update\nbounded by stage data"]
      user_review{"decision: user review"}
      output["output data objects\nseed next stage"]
    end

    subgraph stages["Stage Contract"]
      iface["interface: PlanningStage\nfile: application/stages/base.py\nclass: PlanningStage"]
      draft["stage: DraftStage\nfile: application/stages/draft_stage.py\nclass: DraftStage"]
      plan["stage: PlanStage\nfile: application/stages/plan_stage.py\nclass: PlanStage"]
      epics["stage: EpicsStage\nfile: application/stages/epics_stage.py\nclass: EpicsStage"]
      registry["service: StageRegistry\nfile: application/stage_registry.py\nclass: StageRegistry"]
      runner["service: StageRunner\nfile: application/stage_runner.py\nclass: StageRunner"]
      roll["service: RollRunner\nfile: application/roll.py\nclass: RollRunner"]
    end

    subgraph projection_ports["Application Ports"]
      projection_store["port: ProjectionStore\nfile: application/projections.py\nclass: ProjectionStore"]
    end

    subgraph projection_adapters["Infrastructure Adapters"]
      filesystem_store["adapter: FilesystemProjectionStore\nfile: infrastructure/projection_store.py\nclass: FilesystemProjectionStore"]
    end

    subgraph projections["Events / Projections"]
      events[("event stream\ncanonical facts")]
      enrichment["accepted enrichment\nkeyed by derived slot id"]
      files["documents: projection files\nDRAFT / PLAN / UML / epics"]
      native["documents: native Mermaid projections\nflows / uml / tree"]
      schemas["document: SCHEMAS.md\npasted display projection"]
      guidance["agent guidance\ncurrent stage only"]
      drift["halt: unresolved drift"]
    end

    cmd_start -->|loads first stage| active
    cmd_next -->|accepts reviewed output| active
    cmd_agent -->|requests guidance| active
    cmd_roll -->|refreshes forward| roll
    active -->|resolved by| registry
    registry -->|selects| runner
    runner -->|loads| intake
    runner -->|writes through| projection_store
    intake -->|derives| slots
    slots -->|builds| scaffold
    scaffold -->|writes| files
    scaffold -->|writes| native
    native -->|embedded into| schemas
    files -->|bounds context for| agent_update
    agent_update -->|submitted for| user_review
    user_review -->|approved| output
    user_review -->|needs update| agent_update
    output -->|appended as facts| events
    events -->|selects next stage| active
    events -->|restores enrichment| enrichment
    enrichment -->|reconnects by slot id| slots
    cmd_agent -->|renders| guidance
    draft -. implements .-> iface
    plan -. implements .-> iface
    epics -. implements .-> iface
    draft -->|registered as stage| registry
    plan -->|registered as stage| registry
    epics -->|registered as stage| registry
    roll -->|starts from| draft
    roll -->|delegates execution| runner
    roll -->|loads seed data| intake
    runner -->|halts on drift| drift
    filesystem_store -. implements .-> projection_store

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef loop fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef service fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef adapter fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_start,cmd_next,cmd_agent,cmd_roll command;
    class active,intake,slots,scaffold,agent_update,user_review,output loop;
    class iface,draft,plan,epics,registry,runner,roll service;
    class projection_store port;
    class filesystem_store adapter;
    class events,enrichment,files,native,schemas,guidance,drift output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class PlanningStage {
      <<Interface: application/stages/base.py>>
      +stage_id() str
      +intake_type() type
      +output_type() type
      +derive_slots(StageData) List~DerivedSlot~
      +scaffold(StageData) StageOutput
      +agent_context(StageData) str
      +accept(ReviewData) StageOutput
    }

    class DraftStage {
      <<file:application/stages/draft_stage.py>>
      +stage_id() str
      +derive_slots(StageData) List~DerivedSlot~
      +scaffold(StageData) StageOutput
      +accept(ReviewData) StageOutput
    }

    class PlanStage {
      <<file:application/stages/plan_stage.py>>
      +stage_id() str
      +derive_slots(StageData) List~DerivedSlot~
      +scaffold(StageData) StageOutput
      +accept(ReviewData) StageOutput
    }

    class EpicsStage {
      <<file:application/stages/epics_stage.py>>
      +stage_id() str
      +derive_slots(StageData) List~DerivedSlot~
      +scaffold(StageData) StageOutput
      +accept(ReviewData) StageOutput
    }

    class StageRunner {
      <<file:application/stage_runner.py>>
      +run_current() StageOutput
      +advance_current() StageOutput
      +prepare_agent() str
    }

    class RollRunner {
      <<file:application/roll.py>>
      +start_from_draft() StageOutput
      +continue_children() List~StageOutput~
      +halt_on_drift() None
    }

    class StageRegistry {
      <<file:application/stage_registry.py>>
      +get_current() PlanningStage
      +get_next(PlanningStage) PlanningStage
      +register(PlanningStage) None
    }

    class ProjectionStore {
      <<OutboundPort: application/projections.py>>
      +write_markdown(str, str) None
      +write_mermaid(str, str) None
      +check_sync(str) bool
    }

    class FilesystemProjectionStore {
      <<Adapter: infrastructure/projection_store.py>>
      +port() ProjectionStore
      +write_markdown(str, str) None
      +write_mermaid(str, str) None
      +check_sync(str) bool
    }

    class MarkdownRenderer {
      <<AdapterHelper: infrastructure/markdown_renderer.py>>
      +render_markdown(StageOutput) str
    }

    class CopierRenderer {
      <<AdapterHelper: infrastructure/copier_renderer.py>>
      +render_template(str, StageData) str
    }

    class SchemaPageProjection {
      <<file:application/schema_page.py>>
      +paste_native_sources(List~str~) str
      +render_schemas_md() str
    }

    class StageData {
      <<file:domain/stage_data.py>>
      +str id
      +str stable_identity
      +Mapping~str_to_Any~ values
    }

    class DerivedSlot {
      <<file:domain/stage_data.py>>
      +str id
      +str upstream_identity
      +str stage_id
      +str variant_key
    }

    class StageOutput {
      <<file:domain/stage_data.py>>
      +str next_stage_id
      +List~StageData~ data_objects
    }

    class Enrichment {
      <<file:domain/enrichment.py>>
      +str slot_id
      +Mapping~str_to_Any~ values
    }

    PlanningStage <|.. DraftStage : implements
    PlanningStage <|.. PlanStage : implements
    PlanningStage <|.. EpicsStage : implements

    StageRunner "1" --> "1" StageRegistry : selects stage
    StageRunner "1" --> "1" PlanningStage : runs
    StageRunner "1" --> "1" ProjectionStore : writes projections
    StageRunner "1" --> "1..*" StageData : reads input
    StageRunner "1" --> "0..*" DerivedSlot : derives
    StageRunner "1" --> "1" StageOutput : returns
    StageRunner "1" --> "0..*" Enrichment : preserves
    RollRunner "1" --> "1" DraftStage : starts from
    RollRunner "1" --> "1" StageRunner : advances children
    SchemaPageProjection "1" --> "1" ProjectionStore : publishes
    EpicsStage "1" --> "1" SchemaPageProjection : renders schemas
    FilesystemProjectionStore "1" ..|> "1" ProjectionStore : implements
    FilesystemProjectionStore "1" --> "1" MarkdownRenderer : renders markdown
    FilesystemProjectionStore "1" --> "1" CopierRenderer : renders templates
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "workspace_plan"
    "__init__.py"
    "domain"
      "__init__.py"
      "stage_data.py"
      "enrichment.py"
    "application"
      "__init__.py"
      "projections.py"
      "roll.py"
      "schema_page.py"
      "stage_registry.py"
      "stage_runner.py"
      "stages"
        "__init__.py"
        "base.py"
        "draft_stage.py"
        "plan_stage.py"
        "epics_stage.py"
    "infrastructure"
      "__init__.py"
      "markdown_renderer.py"
      "copier_renderer.py"
      "projection_store.py"
```
