# Event Sourced Core Schemas

## Navigation

- Epic: [Event-Sourced Planning Core](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#event-sourced-planning-core) -> [PLAN.md](../../PLAN.md#event-sourced-core) -> [UML.md](../../UML.md#slug-identity-contract)
- Native sources: [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)
- Siblings: [USER_STORIES.md](USER_STORIES.md)

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected event-sourced use cases.

This epic uses the `eventsourcing` package as the event-sourcing authority. The
planning aggregate extends `eventsourcing.domain.Aggregate`, event classes are
explicit SSOT classes nested under `Plan`, state changes trigger those classes
with `Aggregate.trigger_event`, application persistence and
reconstruction are handled by `eventsourcing.application.Application`, and
durable local storage is configured through `eventsourcing.sqlite`.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#dbeafe", "primaryTextColor": "#172033", "primaryBorderColor": "#2563eb", "secondaryColor": "#e0f2fe", "secondaryBorderColor": "#0284c7", "tertiaryColor": "#f8fafc", "lineColor": "#2563eb"}}}%%
flowchart LR
    subgraph commands["Commands / Queries"]
      cmd_status(["query: workspace plan"])
      cmd_start(["command: workspace plan start TITLE"])
      cmd_next(["command: workspace plan next"])
      cmd_roll(["command: workspace plan roll"])
    end

    subgraph ui_layer["UI"]
      cli["function: plan_command\nfile: ui/cli.py\nfunction: plan_command"]
      templates["templates: current.tmpl / started.tmpl / docs.tmpl / llm.tmpl\nfile: ui/templates"]
    end

    subgraph workspace_layer["Workspace Facade"]
      module["facade: WorkspacePlanModule\nfile: workspace.py\nclass: WorkspacePlanModule"]
      status_report["dto: PlanStatusReport\nfile: workspace.py\nclass: PlanStatusReport"]
    end

    subgraph app_layer["Application"]
      app["service: PlanningApplication\nfile: application.py\nclass: PlanningApplication\nbase: eventsourcing.application.Application"]
      active_guard{"decision: active plan exists?\nfile: application.py\nmethod: _reject_when_active_plan_exists"}
    end

    subgraph domain_layer["Domain"]
      aggregate["aggregate: Plan\nfile: domain/plan.py\nclass: Plan\nbase: eventsourcing.domain.Aggregate"]
      events["event SSOT: Created / StageOutputAccepted / StageAdvanced / DraftUpdated / QuestionChanged / ProjectionRecorded / RollRequested\nfile: domain/plan.py\nnested classes on Plan"]
      questions["model: OpenQuestion / QuestionStatus\nfile: domain/questions.py"]
    end

    subgraph persistence["Library Persistence"]
      sqlite_env["config: EventsourcingSQLitePersistence\nfile: infrastructure/persistence.py\nclass: EventsourcingSQLitePersistence"]
      sqlite_module["library: eventsourcing.sqlite"]
      repository[("repository reconstructs Plan")]
      notification_log[("ordered notification log")]
    end

    subgraph outputs["Outputs"]
      current_template["output: current plan report"]
      started_template["output: started plan"]
      stored_events[("output: durable SQLite event stream")]
    end

    cmd_status -->|invokes| cli
    cmd_start -->|invokes| cli
    cmd_next -->|invokes| cli
    cmd_roll -->|invokes| cli
    cli -->|loads current workspace| module
    module -->|configures per call| sqlite_env
    sqlite_env -->|creates env for| app
    sqlite_env -->|selects| sqlite_module
    cmd_status -->|requests status| module
    module -->|loads active plan| app
    app -->|finds id from| notification_log
    app -->|loads through| repository
    repository -->|reconstructs| aggregate
    module -->|maps plan to| status_report
    status_report -->|renders with| templates
    templates --> current_template

    cmd_start -->|passes title| module
    module -->|calls create_plan| app
    app --> active_guard
    active_guard -->|yes| current_template
    active_guard -->|no| aggregate
    aggregate -->|triggers| events
    app -->|saves| aggregate
    app -->|persists through| sqlite_module
    sqlite_module -->|records| stored_events
    sqlite_module -->|publishes| notification_log
    aggregate -->|renders with| templates
    templates --> started_template

    aggregate -->|triggers matching nested event| events
    events -->|mutate replay state| aggregate

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef ui fill:#dbeafe,stroke:#2563eb,color:#172033;
    classDef workspace fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef app fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef domain fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef persistence fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_status,cmd_start,cmd_change command;
    class cli,templates ui;
    class module,status_report workspace;
    class app,active_guard app;
    class aggregate,events,questions domain;
    class sqlite_env,sqlite_module,repository,notification_log persistence;
    class current_template,started_template,stored_events output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f5f3ff", "primaryTextColor": "#172033", "primaryBorderColor": "#7c3aed", "secondaryColor": "#ede9fe", "secondaryBorderColor": "#6d28d9", "tertiaryColor": "#faf5ff", "lineColor": "#7c3aed"}}}%%
classDiagram
    class PlanningApplication {
      <<Application: application.py>>
      +create_plan(str) Plan
      +get_plan(PlanId) Plan
      +get_active_plan() Plan
      +active_plan_id() PlanId
      +ordered_events() Iterable~DomainEvent~
      -_reject_when_active_plan_exists() None
    }

    class EventsourcingApplication {
      <<library: eventsourcing.application.Application>>
      +save(Aggregate) None
      +repository
      +notification_log
    }

    class Plan {
      <<Aggregate: domain/plan.py>>
      +str title
      +str current_stage
      +str source_use_case_id
      +str source_plan_item_id
      +str created_by_command
      +int schema_version
      +PlanState state
      +bool active
      +str draft_content_hash
      +dict~str_to_OpenQuestion~ questions
      +dict~str_to_ProjectionRecord~ projections
      +dict~str_to_dict~ stage_outputs
      +tuple~str~ roll_requests
      +__init__(str, str, str, str, str, int) None
      +accept_stage_output(str, str, tuple~dict~, tuple~dict~) None
      +advance_stage(str, PlanState, str) None
      +update_draft(str, str) None
      +change_question(str, str, str, QuestionStatus, bool, str) None
      +record_projection(str, str, str) None
      +request_roll(str, str) None
    }

    class EventsourcingAggregate {
      <<library: eventsourcing.domain.Aggregate>>
      +collect_events() list
      +version
    }

    class AggregateCreated {
      <<library: eventsourcing.domain.Aggregate.Created>>
    }

    class AggregateEvent {
      <<library: eventsourcing.domain.Aggregate.Event>>
      +apply(Aggregate) None
    }

    class DomainEvent {
      <<library: eventsourcing.domain.DomainEvent>>
      +UUID originator_id
      +int originator_version
      +datetime timestamp
    }

    class Created {
      <<Plan.Created: domain/plan.py>>
      +str title
      +str current_stage
      +str source_use_case_id
      +str source_plan_item_id
      +str created_by_command
      +int schema_version
    }

    class StageOutputAccepted {
      <<Plan.StageOutputAccepted: domain/plan.py>>
      +str stage
      +str next_stage
      +tuple~dict~ data_objects
      +tuple~dict~ derived_slots
      +apply(Plan) None
    }

    class StageAdvanced {
      <<Plan.StageAdvanced: domain/plan.py>>
      +str stage
      +str state
      +str reason
      +apply(Plan) None
    }

    class DraftUpdated {
      <<Plan.DraftUpdated: domain/plan.py>>
      +str content_hash
      +str source_path
      +apply(Plan) None
    }

    class QuestionChanged {
      <<Plan.QuestionChanged: domain/plan.py>>
      +str question_id
      +str text
      +str explanation
      +str status
      +bool blocking
      +str revisit_stage
      +apply(Plan) None
    }

    class ProjectionRecorded {
      <<Plan.ProjectionRecorded: domain/plan.py>>
      +str projection_id
      +str path
      +str stage
      +apply(Plan) None
    }

    class RollRequested {
      <<Plan.RollRequested: domain/plan.py>>
      +str reason
      +str requested_stage
      +apply(Plan) None
    }

    class PlanState {
      <<Enumeration: domain/plan.py>>
      +str DRAFT$
      +str ACTIVE$
      +str COMPLETE$
    }

    class PlanId {
      <<Value Object: domain/plan.py>>
      +UUID value
      +as_text() str
    }

    class ProjectionRecord {
      <<Value Object: domain/plan.py>>
      +str id
      +str path
      +str stage
    }

    class QuestionStatus {
      <<Enumeration: domain/questions.py>>
      +str OPEN$
      +str RESOLVED$
      +str DEFERRED$
    }

    class OpenQuestion {
      <<Value Object: domain/questions.py>>
      +str id
      +str text
      +str explanation
      +QuestionStatus status
      +bool blocking
      +str revisit_stage
    }

    class EventsourcingSQLitePersistence {
      <<file: infrastructure/persistence.py>>
      +Path database_path
      +environment() dict~str_to_str~
    }

    class EventsourcingSQLite {
      <<library: eventsourcing.sqlite>>
    }

    class PlanStatusReport {
      <<DTO: workspace.py>>
      +Path project_root
      +Path database_path
      +str current_plan_id
      +str title
      +str current_stage
      +str state
      +bool active
      +int version
      +int question_count
      +int projection_count
    }

    class WorkspacePlanModule {
      <<Facade: workspace.py>>
      -Path _project_root
      -Path _database_path
      -EventsourcingSQLitePersistence _persistence
      +__init__(Path, Path) None
      +from_current_workspace() WorkspacePlanModule
      +start(str) Plan
      +next() Plan
      +agent() AgentContext
      +roll() Plan
      +status() PlanStatusReport
      -_planning_application() PlanningApplication
    }

    class plan_command {
      <<Function: ui/cli.py>>
      +plan_command(str, str, bool, bool) None
    }

    class TyperApp {
      <<library: typer.Typer>>
    }

    class TemplateFiles {
      <<templates: ui/templates>>
      +current.tmpl
      +started.tmpl
      +docs.tmpl
      +llm.tmpl
    }

    PlanningApplication --|> EventsourcingApplication : extends
    PlanningApplication "1" --> "1" Plan : saves and reconstructs
    PlanningApplication "1" --> "1" PlanId : resolves active id
    PlanningApplication "1" --> "*" DomainEvent : reads notification log
    Plan --|> EventsourcingAggregate : extends
    Plan "1" --> "1" PlanState : has state
    Plan "1" --> "0..*" OpenQuestion : stores questions
    Plan "1" --> "0..*" ProjectionRecord : stores projections
    Created --|> AggregateCreated : extends
    StageOutputAccepted --|> AggregateEvent : extends
    StageAdvanced --|> AggregateEvent : extends
    DraftUpdated --|> AggregateEvent : extends
    QuestionChanged --|> AggregateEvent : extends
    ProjectionRecorded --|> AggregateEvent : extends
    RollRequested --|> AggregateEvent : extends
    Plan *-- Created : nested class
    Plan *-- StageOutputAccepted : nested class
    Plan *-- StageAdvanced : nested class
    Plan *-- DraftUpdated : nested class
    Plan *-- QuestionChanged : nested class
    Plan *-- ProjectionRecorded : nested class
    Plan *-- RollRequested : nested class
    OpenQuestion "1" --> "1" QuestionStatus : has status
    DomainEvent "*" ..> "1" Plan : mutates
    EventsourcingSQLitePersistence "1" --> "1" EventsourcingSQLite : selects module
    EventsourcingSQLitePersistence "1" --> "1" PlanningApplication : configures
    WorkspacePlanModule "1" --> "1" EventsourcingSQLitePersistence : owns
    WorkspacePlanModule "1" --> "1" PlanningApplication : creates per call
    WorkspacePlanModule "1" --> "1" PlanStatusReport : returns status
    WorkspacePlanModule "1" --> "0..1" Plan : starts or loads
    plan_command "1" --> "1" TyperApp : registered on
    plan_command "1" --> "1" WorkspacePlanModule : calls facade
    plan_command "1" --> "1" TemplateFiles : renders
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
    "application.py"
    "infrastructure"
      "__init__.py"
      "persistence.py"
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
