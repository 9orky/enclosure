---
plan_id: planning-workflow
epic_id: stage-gates-open-questions
title: Stage Gates and Open Questions Schemas
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

# Stage Gates Open Questions Schemas

These schemas are implementation contracts. `tree.mermaid` defines the expected files, `uml.mermaid` defines expected symbols and file ownership, and `flows.mermaid` defines the expected question and gate use cases.

## Flow

```mermaid
%% contract: use_cases
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#e0f2fe", "primaryTextColor": "#172033", "primaryBorderColor": "#0284c7", "lineColor": "#64748b", "tertiaryColor": "#f8fafc"}}}%%
flowchart LR
    subgraph commands["Commands"]
      cmd_add["command: workspace plan question add"]
      cmd_classify["command: workspace plan question classify"]
      cmd_confirm["command: workspace plan question confirm"]
      cmd_check["command: workspace plan check"]
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

    subgraph outputs["Outputs"]
      decision["result: allow or block advance"]
    end

    cmd_add --> uc_add
    cmd_classify --> uc_classify
    cmd_confirm --> uc_confirm
    cmd_check --> uc_gate
    uc_add --> question
    uc_classify --> question
    uc_confirm --> confirmation
    uc_gate --> gate
    question --> gate
    confirmation --> gate
    gate --> decision

    classDef command fill:#e0f2fe,stroke:#0284c7,color:#172033;
    classDef usecase fill:#dcfce7,stroke:#16a34a,color:#172033;
    classDef domain fill:#ffedd5,stroke:#ea580c,color:#172033;
    classDef output fill:#f1f5f9,stroke:#64748b,color:#172033;
    class cmd_add,cmd_classify,cmd_confirm,cmd_check command;
    class uc_add,uc_classify,uc_confirm,uc_gate usecase;
    class question,confirmation,gate domain;
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

    AddOpenQuestion --> OpenQuestion
    ClassifyOpenQuestion --> OpenQuestion
    ConfirmQuestionClassification --> UserConfirmation
    CheckStageGate --> StageGate
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
