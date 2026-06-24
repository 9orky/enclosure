---
plan_id: planning-workflow
epic_id: event-sourced-core
title: Event-Sourced Planning Core Schemas
status: dry-run
stage: epics
source: event_store
generated_from: eventsourcing projection
sync_policy: projection
managed_files:
  - EPIC.md
  - USER_STORIES.md
  - SCHEMAS.md
  - flows.mermaid
  - uml.mermaid
  - tree.mermaid
native_sources:
  flows: flows.mermaid
  uml: uml.mermaid
  tree: tree.mermaid
contract_roles:
  flows: flow contract
  uml: symbol contract
  tree: file contract
---

# Event Sourced Core Schemas

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected event-sourced use cases.

## Flow

```mermaid
%% contract: use_cases
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands / Queries"]
      cmd_start["command: workspace plan start"]
      cmd_append["command: internal append event"]
      cmd_get["query: internal active plan state"]
    end

    subgraph use_cases["Use Cases"]
      uc_start["usecase: StartPlan\nfile: application/use_cases/start_plan.py\nclass: StartPlan"]
      uc_append["usecase: AppendPlanEvent\nfile: application/use_cases/append_plan_event.py\nclass: AppendPlanEvent"]
      uc_get["usecase: GetActivePlan\nfile: application/use_cases/get_active_plan.py\nclass: GetActivePlan"]
    end

    subgraph app_layer["Application"]
      app["application: PlanningApplication"]
    end

    subgraph domain_layer["Domain"]
      aggregate["domain: Plan"]
      events["domain: DomainEvent"]
    end

    subgraph ports["Ports"]
      store["port: EventStore"]
    end

    cmd_start --> uc_start
    cmd_append --> uc_append
    cmd_get --> uc_get
    uc_start --> app
    uc_append --> app
    uc_get --> app
    app --> aggregate
    aggregate --> events
    app --> store

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef app fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef domain fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    class cmd_start,cmd_append,cmd_get command;
    class uc_start,uc_append,uc_get usecase;
    class app app;
    class aggregate,events domain;
    class store port;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class StartPlan {
      <<file:application/use_cases/start_plan.py>>
      +execute()
    }

    class AppendPlanEvent {
      <<file:application/use_cases/append_plan_event.py>>
      +execute(plan_id, event)
    }

    class GetActivePlan {
      <<file:application/use_cases/get_active_plan.py>>
      +execute()
    }

    class PlanningApplication {
      <<file:application/planning_app.py>>
      +create_plan()
      +append_event()
      +get_plan()
    }

    class Plan {
      <<file:domain/plan.py>>
      +str id
      +str title
      +PlanState state
      +bool active
      +advance()
    }

    class DomainEvent {
      <<file:domain/events.py>>
      +UUID originator_id
      +int originator_version
      +datetime timestamp
    }

    StartPlan --> PlanningApplication
    AppendPlanEvent --> PlanningApplication
    GetActivePlan --> PlanningApplication
    PlanningApplication --> Plan
    DomainEvent ..> Plan
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "workspace_plan"
    "domain"
      "plan.py"
      "events.py"
      "questions.py"
    "application"
      "planning_app.py"
      "use_cases"
        "start_plan.py"
        "append_plan_event.py"
        "get_active_plan.py"
    "infrastructure"
      "event_store.py"
```
