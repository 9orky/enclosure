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
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands / Queries"]
      cmd_start(["command: workspace plan start TITLE"])
      cmd_record(["command: internal record plan change"])
      cmd_get(["query: workspace plan"])
    end

    subgraph app_layer["Application"]
      app["service: PlanningApplication\nfile: application.py\nclass: PlanningApplication\nbase: eventsourcing.application.Application"]
    end

    subgraph domain_layer["Domain"]
      aggregate["aggregate: Plan\nfile: domain/plan.py\nclass: Plan\nbase: eventsourcing.domain.Aggregate"]
      events["aggregate event SSOT: Plan.Created / Plan.StageChanged / Plan.QuestionChanged\nfile: domain/plan.py\nclasses carry metadata fields"]
    end

    subgraph persistence["Library Persistence"]
      sqlite_env["config: EventsourcingSQLitePersistence\nfile: infrastructure.py\nclass: EventsourcingSQLitePersistence"]
      sqlite_module["library: eventsourcing.sqlite"]
      notification_log[("ordered notification log")]
    end

    subgraph outputs["Outputs"]
      active_plan["output: active Plan"]
      stored_events[("output: durable SQLite event stream")]
    end

    cmd_start -->|starts new active plan| app
    cmd_record -->|records domain change| app
    cmd_get -->|loads active state| app
    app -->|constructs and saves| aggregate
    aggregate -->|triggers explicit event class| events
    app -->|uses repository to reconstruct| aggregate
    sqlite_env -->|configures| app
    sqlite_env -->|selects| sqlite_module
    app -->|persists through library| sqlite_module
    sqlite_module -->|records| stored_events
    app -->|publishes| notification_log
    aggregate -->|returns| active_plan

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef app fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef domain fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef persistence fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_start,cmd_record,cmd_get command;
    class app app;
    class aggregate,events domain;
    class sqlite_env,sqlite_module,notification_log persistence;
    class active_plan,stored_events output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class PlanningApplication {
      <<Application: application.py>>
      +create_plan(str) Plan
      +apply_change(PlanId, PlanChange) Plan
      +get_plan(PlanId) Plan
      +get_active_plan() Plan
      +ordered_events() Iterable~DomainEvent~
    }

    class EventsourcingApplication {
      <<library: eventsourcing.application.Application>>
      +save(Aggregate) None
      +repository
      +notification_log
    }

    class Plan {
      <<Aggregate: domain/plan.py>>
      +UUID id
      +str title
      +PlanState state
      +bool active
      +str current_stage
      +change_stage(str) None
      +update_draft(str) None
      +change_question(str, str, str, str, bool, str) None
      +register_projection(str, str) None
      +request_roll(str) None
    }

    class EventsourcingAggregate {
      <<library: eventsourcing.domain.Aggregate>>
      +collect_events() list
      +version
    }

    class DomainEvent {
      <<library: eventsourcing.domain.DomainEvent>>
      +UUID originator_id
      +int originator_version
      +datetime timestamp
    }

    class PlanCreated {
      <<Event SSOT: domain/plan.py>>
      +str title
      +str current_stage
      +str source_plan_item_id
      +str source_use_case_id
    }

    class PlanStageChanged {
      <<Event SSOT: domain/plan.py>>
      +str stage
      +str reason
    }

    class PlanQuestionChanged {
      <<Event SSOT: domain/plan.py>>
      +str question_id
      +str text
      +str explanation
      +str status
      +bool blocking
      +str revisit_stage
    }

    class PlanState {
      <<Enumeration: domain/plan.py>>
      +str DRAFT$
      +str ACTIVE$
      +str COMPLETE$
    }

    class PlanChange {
      <<file:domain/events.py>>
      +apply(Plan) None
    }

    class EventsourcingSQLitePersistence {
      <<file:infrastructure.py>>
      +environment() dict
    }

    class EventsourcingSQLite {
      <<library: eventsourcing.sqlite>>
    }

    PlanningApplication --|> EventsourcingApplication : extends
    PlanningApplication "1" --> "1" Plan : saves and reconstructs
    PlanningApplication "1" --> "*" DomainEvent : reads notification log
    Plan --|> EventsourcingAggregate : extends
    Plan "1" --> "1" PlanState : has state
    PlanCreated --|> DomainEvent : extends
    PlanStageChanged --|> DomainEvent : extends
    PlanQuestionChanged --|> DomainEvent : extends
    PlanChange "1" --> "1" Plan : invokes event method
    DomainEvent "*" ..> "1" Plan : mutates
    EventsourcingSQLitePersistence "1" --> "1" EventsourcingSQLite : selects module
    EventsourcingSQLitePersistence "1" --> "1" PlanningApplication : configures
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "features/workspace/plan"
    "__init__.py"
    "domain"
      "__init__.py"
      "plan.py"
      "events.py"
      "questions.py"
    "application.py"
    "infrastructure.py"
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
