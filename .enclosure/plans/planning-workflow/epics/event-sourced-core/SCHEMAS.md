# Event Sourced Core Schemas

## Navigation

- Epic: [Event-Sourced Planning Core](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#event-sourced-planning-core) -> [PLAN.md](../../PLAN.md#event-sourced-core) -> [UML.md](../../UML.md#slug-identity-contract)
- Native sources: [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)
- Siblings: [USER_STORIES.md](USER_STORIES.md)

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected event-sourced use cases.

## Flow

```mermaid
%% contract: use_cases
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands / Queries"]
      cmd_start(["command: workspace plan start"])
      cmd_append(["command: internal append event"])
      cmd_get(["query: internal active plan state"])
    end

    subgraph use_cases["Use Cases"]
      uc_start["usecase: StartPlan\nfile: application/use_cases/start_plan.py\nclass: StartPlan"]
      uc_append["usecase: AppendPlanEvent\nfile: application/use_cases/append_plan_event.py\nclass: AppendPlanEvent"]
      uc_get["usecase: GetActivePlan\nfile: application/use_cases/get_active_plan.py\nclass: GetActivePlan"]
    end

    subgraph app_layer["Application"]
      app["service: PlanningApplication\nfile: application/planning_app.py\nclass: PlanningApplication"]
    end

    subgraph domain_layer["Domain"]
      aggregate["domain: Plan\nfile: domain/plan.py\nclass: Plan"]
      events["domain event: DomainEvent\nfile: domain/events.py\nclass: DomainEvent"]
    end

    subgraph ports["Application Ports"]
      store["port: EventStore\nfile: application/ports.py\nclass: EventStore"]
    end

    subgraph adapters["Infrastructure Adapters"]
      sqlite_store["adapter: SQLiteEventStore\nfile: infrastructure/event_store.py\nclass: SQLiteEventStore"]
    end

    subgraph outputs["Outputs"]
      active_plan["output: active Plan"]
      stored_events[("output: durable event stream")]
    end

    cmd_start -->|starts new active plan| uc_start
    cmd_append -->|records domain fact| uc_append
    cmd_get -->|loads active state| uc_get
    uc_start -->|invokes| app
    uc_append -->|invokes| app
    uc_get -->|invokes| app
    app -->|reconstructs| aggregate
    aggregate -->|emits| events
    app -->|persists through| store
    sqlite_store -. implements .-> store
    aggregate -->|returns| active_plan
    events -->|appended to| stored_events

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef app fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef domain fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef adapter fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_start,cmd_append,cmd_get command;
    class uc_start,uc_append,uc_get usecase;
    class app app;
    class aggregate,events domain;
    class store port;
    class sqlite_store adapter;
    class active_plan,stored_events output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class StartPlan {
      <<file:application/use_cases/start_plan.py>>
      +execute() Plan
    }

    class AppendPlanEvent {
      <<file:application/use_cases/append_plan_event.py>>
      +execute(PlanId, DomainEvent) Plan
    }

    class GetActivePlan {
      <<file:application/use_cases/get_active_plan.py>>
      +execute() Plan
    }

    class PlanningApplication {
      <<file:application/planning_app.py>>
      +create_plan() Plan
      +append_event(PlanId, DomainEvent) Plan
      +get_plan(PlanId) Plan
    }

    class EventStore {
      <<OutboundPort: application/ports.py>>
      +append(DomainEvent) None
      +load(PlanId) List~DomainEvent~
      +iter_events(PlanId) Iterable~DomainEvent~
    }

    class SQLiteEventStore {
      <<Adapter: infrastructure/event_store.py>>
      +port() EventStore
      +append(DomainEvent) None
      +load(PlanId) List~DomainEvent~
      +iter_events(PlanId) Iterable~DomainEvent~
    }

    class Plan {
      <<file:domain/plan.py>>
      +str id
      +str title
      +PlanState state
      +bool active
      +advance(DomainEvent) Plan
    }

    class DomainEvent {
      <<file:domain/events.py>>
      +UUID originator_id
      +int originator_version
      +datetime timestamp
    }

    class PlanState {
      <<Enumeration: domain/plan.py>>
      +str DRAFT$
      +str ACTIVE$
      +str COMPLETE$
    }

    StartPlan "1" --> "1" PlanningApplication : invokes
    AppendPlanEvent "1" --> "1" PlanningApplication : invokes
    GetActivePlan "1" --> "1" PlanningApplication : invokes
    PlanningApplication "1" --> "1" Plan : reconstructs
    PlanningApplication "1" --> "1" EventStore : persists events
    SQLiteEventStore "1" ..|> "1" EventStore : implements
    Plan "1" --> "1" PlanState : has state
    DomainEvent "*" ..> "1" Plan : mutates
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
      "plan.py"
      "events.py"
      "questions.py"
    "application"
      "__init__.py"
      "ports.py"
      "planning_app.py"
      "use_cases"
        "__init__.py"
        "start_plan.py"
        "append_plan_event.py"
        "get_active_plan.py"
    "infrastructure"
      "__init__.py"
      "event_store.py"
```
