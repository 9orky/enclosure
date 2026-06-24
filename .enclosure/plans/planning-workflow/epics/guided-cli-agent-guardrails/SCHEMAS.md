# Guided Cli Agent Guardrails Schemas

## Navigation

- Epic: [Guided CLI and Agent Guardrails](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#guided-cli-and-agent-guardrails) -> [PLAN.md](../../PLAN.md#guided-cli-agent-guardrails) -> [UML.md](../../UML.md#slug-identity-contract)
- Native sources: [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)
- Siblings: [USER_STORIES.md](USER_STORIES.md)

These schemas are implementation contracts shown as a display projection. The
native sources are `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`; during
projection updates their content is pasted into the sections below.

`tree.mermaid` defines the expected files, `uml.mermaid` defines expected
symbols and file ownership, and `flows.mermaid` defines the expected
parameterless CLI command loop.

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

    subgraph use_cases["Use Cases"]
      uc_start["usecase: RunPlanStart\nfile: application/use_cases/run_plan_start.py\nclass: RunPlanStart"]
      uc_next["usecase: RunPlanNext\nfile: application/use_cases/run_plan_next.py\nclass: RunPlanNext"]
      uc_agent["usecase: PrepareAgentGuidance\nfile: application/use_cases/prepare_agent_guidance.py\nclass: PrepareAgentGuidance"]
      uc_roll["usecase: RunPlanRoll\nfile: application/use_cases/run_plan_roll.py\nclass: RunPlanRoll"]
    end

    subgraph services["Services"]
      app["application: PlanningApplication\nowned by event-sourced-core"]
      guidance["service: AgentGuidance\nfile: application/agent_guidance.py\nclass: AgentGuidance"]
      next_actions["service: NextActionService\nfile: application/next_actions.py\nclass: NextActionService"]
    end

    subgraph ports["Application Ports"]
      stage_runner_port["port: StageRunnerPort\nfile: application/workflow_ports.py\nclass: StageRunnerPort"]
      roll_runner_port["port: RollRunnerPort\nfile: application/workflow_ports.py\nclass: RollRunnerPort"]
      gate_port["port: StageGatePort\nfile: application/workflow_ports.py\nclass: StageGatePort"]
    end

    subgraph implementations["External Implementations"]
      stage_runner["implementation: StageRunner\nexternal: projected-documents/application/stage_runner.py\nclass: StageRunner"]
      roll_runner["implementation: RollRunner\nexternal: projected-documents/application/roll.py\nclass: RollRunner"]
      gate["implementation: CheckStageGate\nexternal: stage-gates-open-questions/application/use_cases/check_stage_gate.py\nclass: CheckStageGate"]
    end

    subgraph outputs["Outputs"]
      allowed{"decision: command allowed?"}
      output["projection: allowed commands"]
      blocked["halt: command blocked"]
    end

    cmd_start -->|dispatches| uc_start
    cmd_next -->|dispatches| uc_next
    cmd_agent -->|dispatches| uc_agent
    cmd_roll -->|dispatches| uc_roll
    uc_start -->|creates plan through| app
    uc_next -->|advances through| stage_runner_port
    uc_next -->|checks gate through| gate_port
    uc_agent -->|renders| guidance
    uc_roll -->|refreshes through| roll_runner_port
    guidance -->|constrains| next_actions
    stage_runner_port -->|reports state to| next_actions
    roll_runner_port -->|reports state to| next_actions
    gate_port -->|reports gate to| next_actions
    stage_runner -. implements .-> stage_runner_port
    roll_runner -. implements .-> roll_runner_port
    gate -. implements .-> gate_port
    next_actions -->|evaluates| allowed
    allowed -->|allowed| output
    allowed -->|blocked| blocked

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef service fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef port fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef external fill:#f1f5f9,stroke:#64748b,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_start,cmd_next,cmd_agent,cmd_roll command;
    class uc_start,uc_next,uc_agent,uc_roll usecase;
    class app,guidance,next_actions service;
    class stage_runner_port,roll_runner_port,gate_port port;
    class stage_runner,roll_runner,gate external;
    class allowed,output,blocked output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f5f3ff", "primaryTextColor": "#172033", "primaryBorderColor": "#7c3aed", "secondaryColor": "#ede9fe", "secondaryBorderColor": "#6d28d9", "tertiaryColor": "#faf5ff", "lineColor": "#7c3aed"}}}%%
classDiagram
    class RunPlanStart {
      <<file:application/use_cases/run_plan_start.py>>
      +execute() CommandResult
    }

    class RunPlanNext {
      <<file:application/use_cases/run_plan_next.py>>
      +execute() CommandResult
    }

    class PrepareAgentGuidance {
      <<file:application/use_cases/prepare_agent_guidance.py>>
      +execute() AgentGuidance
    }

    class RunPlanRoll {
      <<file:application/use_cases/run_plan_roll.py>>
      +execute() CommandResult
    }

    class PlanCli {
      <<file:ui/cli.py>>
      +start() int
      +next() int
      +agent() int
      +roll() int
    }

    class NextActionService {
      <<file:application/next_actions.py>>
      +allowed_commands() List~str~
      +blocked_commands() List~str~
    }

    class AgentGuidance {
      <<file:application/agent_guidance.py>>
      +render_context() str
      +requires_confirmation() bool
    }

    class StageRunnerPort {
      <<OutboundPort: application/workflow_ports.py>>
      +advance_current() StageOutput
      +prepare_agent() str
    }

    class RollRunnerPort {
      <<OutboundPort: application/workflow_ports.py>>
      +start_from_draft() StageOutput
    }

    class StageGatePort {
      <<OutboundPort: application/workflow_ports.py>>
      +check(PlanId) StageGateDecision
    }

    class StageRunner {
      <<external:projected-documents/application/stage_runner.py>>
      +advance_current() StageOutput
    }

    class RollRunner {
      <<external:projected-documents/application/roll.py>>
      +start_from_draft() StageOutput
    }

    class CheckStageGate {
      <<external:stage-gates-open-questions/application/use_cases/check_stage_gate.py>>
      +execute(PlanId) StageGateDecision
    }

    PlanCli "1" --> "1" RunPlanStart : dispatches start
    PlanCli "1" --> "1" RunPlanNext : dispatches next
    PlanCli "1" --> "1" PrepareAgentGuidance : dispatches agent
    PlanCli "1" --> "1" RunPlanRoll : dispatches roll
    RunPlanStart "1" --> "1" NextActionService : reports moves
    RunPlanNext "1" --> "1" NextActionService : reports moves
    RunPlanNext "1" --> "1" StageRunnerPort : advances stage
    RunPlanNext "1" --> "1" StageGatePort : checks gate
    PrepareAgentGuidance "1" --> "1" AgentGuidance : renders context
    RunPlanRoll "1" --> "1" RollRunnerPort : refreshes projections
    RunPlanRoll "1" --> "1" NextActionService : reports moves
    StageRunner "1" ..|> "1" StageRunnerPort : implements
    RollRunner "1" ..|> "1" RollRunnerPort : implements
    CheckStageGate "1" ..|> "1" StageGatePort : implements
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#ecfdf5", "primaryTextColor": "#064e3b", "primaryBorderColor": "#059669", "labelColor": "#064e3b", "lineColor": "#059669", "tertiaryColor": "#f0fdf4"}}}%%
treeView-beta
  "workspace_plan"
    "__init__.py"
    "application"
      "__init__.py"
      "workflow_ports.py"
      "next_actions.py"
      "agent_guidance.py"
      "use_cases"
        "__init__.py"
        "run_plan_start.py"
        "run_plan_next.py"
        "prepare_agent_guidance.py"
        "run_plan_roll.py"
    "ui"
      "__init__.py"
      "cli.py"
      "output.py"
```
