# Stage Gates Open Questions Schemas

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected question and gate use cases.

## Flow

```mermaid
%% contract: flow
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph signals["Stage Loop Signals"]
      signal_add["signal: agent or user raised question"]
      signal_classify["signal: classification proposed"]
      signal_confirm["signal: user confirmed unblock"]
      signal_check["signal: next requested gate check"]
    end

    subgraph use_cases["Use Cases"]
      uc_add["usecase: AddOpenQuestion\nfile: application/use_cases/add_open_question.py\nclass: AddOpenQuestion"]
      uc_classify["usecase: ClassifyOpenQuestion\nfile: application/use_cases/classify_open_question.py\nclass: ClassifyOpenQuestion"]
      uc_confirm["usecase: ConfirmQuestionClassification\nfile: application/use_cases/confirm_question_classification.py\nclass: ConfirmQuestionClassification"]
      uc_gate["usecase: CheckStageGate\nfile: application/use_cases/check_stage_gate.py\nclass: CheckStageGate"]
    end

    subgraph domain_layer["Domain"]
      question["domain: OpenQuestion"]
      confirmation["domain: UserConfirmation"]
      gate["domain: StageGate"]
    end

    subgraph application_contracts["Application Contracts"]
      question_commands["service: QuestionCommandService\nfile: application/question_commands.py\nclass: QuestionCommandService"]
      gate_policy["interface: StageGatePolicy\nfile: application/gate_checks.py\nclass: StageGatePolicy"]
      default_gate_policy["implementation: DefaultStageGatePolicy\nfile: application/gate_checks.py\nclass: DefaultStageGatePolicy"]
    end

    subgraph outputs["Outputs"]
      decision["result: allow or block advance"]
    end

    signal_add --> uc_add
    signal_classify --> uc_classify
    signal_confirm --> uc_confirm
    signal_check --> uc_gate
    uc_add --> question_commands
    uc_classify --> question_commands
    uc_confirm --> question_commands
    uc_gate --> gate_policy
    question_commands --> question
    question_commands --> confirmation
    gate_policy --> gate
    default_gate_policy -. implements .-> gate_policy
    question --> gate
    confirmation --> gate
    gate --> decision

    classDef signal fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef domain fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef service fill:#fef9c3,stroke:#ca8a04,color:#172033;
    classDef interface fill:#f3e8ff,stroke:#9333ea,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class signal_add,signal_classify,signal_confirm,signal_check signal;
    class uc_add,uc_classify,uc_confirm,uc_gate usecase;
    class question,confirmation,gate domain;
    class question_commands,default_gate_policy service;
    class gate_policy interface;
    class decision output;
```

## UML

```mermaid
%% contract: symbols
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#eef2ff", "primaryTextColor": "#172033", "primaryBorderColor": "#64748b", "lineColor": "#64748b"}}}%%
classDiagram
    class AddOpenQuestion {
      <<file:application/use_cases/add_open_question.py>>
      +execute(question, explanation)
    }

    class ClassifyOpenQuestion {
      <<file:application/use_cases/classify_open_question.py>>
      +execute(question_id, status)
    }

    class ConfirmQuestionClassification {
      <<file:application/use_cases/confirm_question_classification.py>>
      +execute(question_id)
    }

    class CheckStageGate {
      <<file:application/use_cases/check_stage_gate.py>>
      +execute(plan_id)
    }

    class OpenQuestion {
      <<file:domain/gates.py>>
      +str question
      +str explanation
      +QuestionStatus status
      +str decision
      +str revisit_at
    }

    class StageGate {
      <<file:domain/gates.py>>
      +check()
      +blocking_questions()
    }

    class UserConfirmation {
      <<file:domain/gates.py>>
      +confirm_classification()
    }

    class QuestionCommandService {
      <<file:application/question_commands.py>>
      +add(question, explanation)
      +classify(question_id, status)
      +confirm(question_id)
    }

    class StageGatePolicy {
      <<Protocol: application/gate_checks.py>>
      +check(plan_id)
      +blocking_questions(plan_id)
    }

    class DefaultStageGatePolicy {
      <<file:application/gate_checks.py>>
      +check(plan_id)
      +blocking_questions(plan_id)
    }

    AddOpenQuestion --> QuestionCommandService
    ClassifyOpenQuestion --> QuestionCommandService
    ConfirmQuestionClassification --> QuestionCommandService
    CheckStageGate --> StageGatePolicy
    QuestionCommandService --> OpenQuestion
    QuestionCommandService --> UserConfirmation
    DefaultStageGatePolicy ..|> StageGatePolicy
    DefaultStageGatePolicy --> StageGate
    StageGate --> OpenQuestion
    UserConfirmation --> OpenQuestion
```

## Tree

```mermaid
%% contract: files
%%{init: {"theme": "base", "themeVariables": {"labelColor": "#172033", "lineColor": "#64748b"}}}%%
treeView-beta
  "workspace_plan"
    "domain"
      "gates.py"
      "question_status.py"
    "application"
      "gate_checks.py"
      "question_commands.py"
      "use_cases"
        "add_open_question.py"
        "classify_open_question.py"
        "confirm_question_classification.py"
        "check_stage_gate.py"
```
