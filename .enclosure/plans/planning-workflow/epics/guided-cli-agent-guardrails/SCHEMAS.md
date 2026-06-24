---
plan_id: planning-workflow
epic_id: guided-cli-agent-guardrails
title: Guided CLI and Agent Guardrails Schemas
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
  flows: use-case contract
  uml: symbol contract
  tree: file contract
---

# Guided Cli Agent Guardrails Schemas

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected CLI and agent-guidance use cases.

## Flow

```mermaid
%% contract: use_cases
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands"]
      cmd_status["command: workspace plan status"]
      cmd_next["command: workspace plan next"]
      cmd_agent["command: workspace plan agent"]
      cmd_allowed["internal: render allowed actions"]
    end

    subgraph use_cases["Use Cases"]
      uc_status["usecase: ShowPlanStatus\nfile: application/use_cases/show_plan_status.py\nclass: ShowPlanStatus"]
      uc_next["usecase: RunPlanNext\nfile: application/use_cases/run_plan_next.py\nclass: RunPlanNext"]
      uc_agent["usecase: PrepareAgentGuidance\nfile: application/use_cases/prepare_agent_guidance.py\nclass: PrepareAgentGuidance"]
      uc_allowed["usecase: RenderAllowedActions\nfile: application/use_cases/render_allowed_actions.py\nclass: RenderAllowedActions"]
    end

    subgraph services["Services"]
      app["application: PlanningApplication"]
      guidance["service: AgentGuidance"]
      next_actions["service: NextActionService"]
    end

    subgraph external_use_cases["External Use Cases"]
      importer["external usecase: ImportInputBlocks"]
      gate["external usecase: CheckStageGate"]
    end

    subgraph outputs["Outputs"]
      output["projection: allowed commands"]
    end

    cmd_status --> uc_status
    cmd_next --> uc_next
    cmd_agent --> uc_agent
    cmd_allowed --> uc_allowed
    uc_status --> app
    uc_next --> importer
    uc_next --> gate
    uc_agent --> guidance
    uc_allowed --> next_actions
    guidance --> next_actions
    next_actions --> output

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef service fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef external fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_status,cmd_next,cmd_agent,cmd_allowed command;
    class uc_status,uc_next,uc_agent,uc_allowed usecase;
    class app,guidance,next_actions service;
    class importer,gate external;
    class output output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class ShowPlanStatus {
      <<file:application/use_cases/show_plan_status.py>>
      +execute()
    }

    class RunPlanNext {
      <<file:application/use_cases/run_plan_next.py>>
      +execute()
    }

    class PrepareAgentGuidance {
      <<file:application/use_cases/prepare_agent_guidance.py>>
      +execute()
    }

    class RenderAllowedActions {
      <<file:application/use_cases/render_allowed_actions.py>>
      +execute(plan_state)
    }

    class PlanCli {
      <<file:ui/cli.py>>
      +status()
      +start()
      +next()
      +agent()
    }

    class NextActionService {
      <<file:application/next_actions.py>>
      +allowed_commands()
      +blocked_commands()
    }

    class AgentGuidance {
      <<file:application/agent_guidance.py>>
      +render_context()
      +requires_confirmation()
    }

    PlanCli --> ShowPlanStatus
    PlanCli --> RunPlanNext
    PlanCli --> PrepareAgentGuidance
    ShowPlanStatus --> NextActionService
    RunPlanNext --> NextActionService
    PrepareAgentGuidance --> AgentGuidance
    RenderAllowedActions --> NextActionService
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "workspace_plan"
    "ui"
      "cli.py"
      "output.py"
    "application"
      "next_actions.py"
      "agent_guidance.py"
      "use_cases"
        "show_plan_status.py"
        "run_plan_next.py"
        "prepare_agent_guidance.py"
        "render_allowed_actions.py"
```
