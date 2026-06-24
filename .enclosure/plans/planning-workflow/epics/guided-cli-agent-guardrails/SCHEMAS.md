# Guided Cli Agent Guardrails Schemas

These schemas are implementation contracts shown as a display projection. The
native sources are `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`; during
projection updates their content is pasted into the sections below.

`tree.mermaid` defines the expected files, `uml.mermaid` defines expected
symbols and file ownership, and `flows.mermaid` defines the expected
parameterless CLI command loop.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Parameterless Commands"]
      cmd_start["command: workspace plan start"]
      cmd_next["command: workspace plan next"]
      cmd_agent["command: workspace plan agent"]
      cmd_roll["command: workspace plan roll"]
    end

    subgraph use_cases["Use Cases"]
      uc_start["usecase: RunPlanStart\nfile: application/use_cases/run_plan_start.py\nclass: RunPlanStart"]
      uc_next["usecase: RunPlanNext\nfile: application/use_cases/run_plan_next.py\nclass: RunPlanNext"]
      uc_agent["usecase: PrepareAgentGuidance\nfile: application/use_cases/prepare_agent_guidance.py\nclass: PrepareAgentGuidance"]
      uc_roll["usecase: RunPlanRoll\nfile: application/use_cases/run_plan_roll.py\nclass: RunPlanRoll"]
    end

    subgraph services["Services"]
      app["application: PlanningApplication"]
      guidance["service: AgentGuidance"]
      next_actions["service: NextActionService"]
    end

    subgraph external_services["External Services"]
      stage_runner["external service: StageRunner"]
      roll_runner["external service: RollRunner"]
      gate["external usecase: CheckStageGate"]
    end

    subgraph outputs["Outputs"]
      output["projection: allowed commands"]
    end

    cmd_start --> uc_start
    cmd_next --> uc_next
    cmd_agent --> uc_agent
    cmd_roll --> uc_roll
    uc_start --> app
    uc_next --> stage_runner
    uc_next --> gate
    uc_agent --> guidance
    uc_roll --> roll_runner
    guidance --> next_actions
    stage_runner --> next_actions
    roll_runner --> next_actions
    next_actions --> output

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef service fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef external fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_start,cmd_next,cmd_agent,cmd_roll command;
    class uc_start,uc_next,uc_agent,uc_roll usecase;
    class app,guidance,next_actions service;
    class stage_runner,roll_runner,gate external;
    class output output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class RunPlanStart {
      <<file:application/use_cases/run_plan_start.py>>
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

    class RunPlanRoll {
      <<file:application/use_cases/run_plan_roll.py>>
      +execute()
    }

    class PlanCli {
      <<file:ui/cli.py>>
      +start()
      +next()
      +agent()
      +roll()
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

    class StageRunner {
      <<external:projected-documents/application/stage_runner.py>>
      +advance_current()
    }

    class RollRunner {
      <<external:projected-documents/application/roll.py>>
      +start_from_draft()
    }

    PlanCli --> RunPlanStart
    PlanCli --> RunPlanNext
    PlanCli --> PrepareAgentGuidance
    PlanCli --> RunPlanRoll
    RunPlanStart --> NextActionService
    RunPlanNext --> NextActionService
    RunPlanNext --> StageRunner
    PrepareAgentGuidance --> AgentGuidance
    RunPlanRoll --> RollRunner
    RunPlanRoll --> NextActionService
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
        "run_plan_start.py"
        "run_plan_next.py"
        "prepare_agent_guidance.py"
        "run_plan_roll.py"
```
