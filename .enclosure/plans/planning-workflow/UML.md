# Planning Workflow Technical View

## Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DraftStage
    DraftStage --> PlanStage: next accepts six draft use cases
    PlanStage --> EpicStage: next accepts six plan items
    EpicStage --> Complete: next accepts six epic packages

    DraftStage --> DraftStage: answer draft Open Questions
    PlanStage --> PlanStage: answer plan Open Questions
    EpicStage --> EpicStage: answer epic Open Questions
    Complete --> DraftStage: roll recomputes from draft seed
```

## Slug Identity Contract

```mermaid
flowchart LR
    subgraph draft["DRAFT.md use_case_id"]
      D0["hexagonal-foundation"]
      D1["event-sourced-core"]
      D2["projected-documents"]
      D3["stage-gates-open-questions"]
      D4["guided-cli-agent-guardrails"]
      D5["schema-contract-verification"]
    end

    subgraph plan["PLAN.md plan_item_id"]
      P0["hexagonal-foundation"]
      P1["event-sourced-core"]
      P2["projected-documents"]
      P3["stage-gates-open-questions"]
      P4["guided-cli-agent-guardrails"]
      P5["schema-contract-verification"]
    end

    subgraph epic["epics/<epic_id>/"]
      E0["hexagonal-foundation"]
      E1["event-sourced-core"]
      E2["projected-documents"]
      E3["stage-gates-open-questions"]
      E4["guided-cli-agent-guardrails"]
      E5["schema-contract-verification"]
    end

    D0 --> P0 --> E0
    D1 --> P1 --> E1
    D2 --> P2 --> E2
    D3 --> P3 --> E3
    D4 --> P4 --> E4
    D5 --> P5 --> E5
```

## Stage Procedure

```mermaid
flowchart LR
    Current["current stage\nselected from events"] --> Input["stage input data"]
    Input --> Slots["derive slots\nslug + stage id + variant key"]
    Slots --> Scaffold["scaffold projection"]
    Scaffold --> Agent["agent fills prose\nquestions and contracts"]
    Agent --> User["user fills answers\nand corrections"]
    User --> Parse["parse review"]
    Parse --> Gate["validate and gate"]
    Gate --> Accept["next accepts output"]
    Accept --> Events["append events"]
    Events --> Project["render next projection"]
    Project --> Current

    Gate --> Blocked["blocked questions\nor drift"]
```

## Stage Objects

```mermaid
classDiagram
    class DraftSeed {
      +str title
      +str abstract
      +List~DraftUseCase~ use_cases
      +List~OpenQuestion~ answered_questions
    }

    class DraftUseCase {
      +str use_case_id
      +str name
      +str description
      +List~str~ constraints
      +str agent_prose
    }

    class PlanContract {
      +str purpose
      +str value
      +List~PlanItem~ items
      +List~PlanDecision~ decisions
      +List~OpenQuestion~ answered_questions
    }

    class PlanItem {
      +str plan_item_id
      +str source_use_case_id
      +str name
      +str intent
      +List~str~ accepted_constraints
      +str planned_outcome
      +List~str~ acceptance_notes
    }

    class EpicPackage {
      +str epic_id
      +str source_plan_item_id
      +str title
      +str value
      +str outcome
      +List~str~ scope
      +List~str~ out_of_scope
      +List~UserStory~ stories
      +SchemaContracts schemas
    }

    class SchemaContracts {
      +str flows_mermaid
      +str uml_mermaid
      +str tree_mermaid
      +str schemas_md
    }

    class OpenQuestion {
      +str id
      +str question
      +str explanation
      +str answer
      +QuestionStatus status
      +str revisit_at
    }

    DraftSeed "1" --> "6" DraftUseCase : contains
    PlanContract "1" --> "6" PlanItem : contains
    EpicPackage "1" --> "1" SchemaContracts : owns
    PlanItem "1" --> "1" DraftUseCase : source_use_case_id
    EpicPackage "1" --> "1" PlanItem : source_plan_item_id
```

## Example Object Chain

```mermaid
flowchart TD
    U0["DraftUseCase\nuse_case_id: hexagonal-foundation"] --> I0["PlanItem\nplan_item_id: hexagonal-foundation"] --> X0["EpicPackage\nepic_id: hexagonal-foundation"]
    U1["DraftUseCase\nuse_case_id: event-sourced-core"] --> I1["PlanItem\nplan_item_id: event-sourced-core"] --> X1["EpicPackage\nepic_id: event-sourced-core"]
    U2["DraftUseCase\nuse_case_id: projected-documents"] --> I2["PlanItem\nplan_item_id: projected-documents"] --> X2["EpicPackage\nepic_id: projected-documents"]
    U3["DraftUseCase\nuse_case_id: stage-gates-open-questions"] --> I3["PlanItem\nplan_item_id: stage-gates-open-questions"] --> X3["EpicPackage\nepic_id: stage-gates-open-questions"]
    U4["DraftUseCase\nuse_case_id: guided-cli-agent-guardrails"] --> I4["PlanItem\nplan_item_id: guided-cli-agent-guardrails"] --> X4["EpicPackage\nepic_id: guided-cli-agent-guardrails"]
    U5["DraftUseCase\nuse_case_id: schema-contract-verification"] --> I5["PlanItem\nplan_item_id: schema-contract-verification"] --> X5["EpicPackage\nepic_id: schema-contract-verification"]
```

## Artifact Projection

```mermaid
flowchart TD
    Commands["enclosure workspace plan\nstart title / next / agent / roll"] --> App["PlanningApplication"]
    App --> Store["SQLite event store\n.enclosure/.cache/plans.sqlite"]
    Store --> Aggregate["Plan aggregate"]

    Aggregate --> Draft["DRAFT.md\nsix use cases"]
    Aggregate --> Plan["PLAN.md\nsix plan items"]
    Aggregate --> RootUML["UML.md\nstage and id contracts"]

    Plan --> Epics["six epic packages"]
    Epics --> E0["epics/hexagonal-foundation"]
    Epics --> E1["epics/event-sourced-core"]
    Epics --> E2["epics/projected-documents"]
    Epics --> E3["epics/stage-gates-open-questions"]
    Epics --> E4["epics/guided-cli-agent-guardrails"]
    Epics --> E5["epics/schema-contract-verification"]

    E0 --> S0["flows.mermaid\numl.mermaid\ntree.mermaid\nSCHEMAS.md"]
    E1 --> S1["flows.mermaid\numl.mermaid\ntree.mermaid\nSCHEMAS.md"]
    E2 --> S2["flows.mermaid\numl.mermaid\ntree.mermaid\nSCHEMAS.md"]
    E3 --> S3["flows.mermaid\numl.mermaid\ntree.mermaid\nSCHEMAS.md"]
    E4 --> S4["flows.mermaid\numl.mermaid\ntree.mermaid\nSCHEMAS.md"]
    E5 --> S5["flows.mermaid\numl.mermaid\ntree.mermaid\nSCHEMAS.md"]
```

## Stage Interface

```mermaid
classDiagram
    class PlanningStage {
      <<Interface: application/stages/base.py>>
      +stage_id() str
      +input_type() type
      +output_type() type
      +projection_paths(StageContext) List~ArtifactRef~
      +derive_slots(StageContext) List~DerivedSlot~
      +scaffold(StageContext) List~ProjectedArtifact~
      +agent_context(StageContext) AgentContext
      +parse_review(List~ProjectedArtifact~) ReviewData
      +validate_review(ReviewData) ValidationResult
      +accept(StageContext, ReviewData) StageOutput
    }

    class DraftStage {
      <<file:application/stages/draft_stage.py>>
      +stage_id() str
      +accept(StageContext, ReviewData) StageOutput
    }

    class PlanStage {
      <<file:application/stages/plan_stage.py>>
      +stage_id() str
      +accept(StageContext, ReviewData) StageOutput
    }

    class EpicStage {
      <<file:application/stages/epic_stage.py>>
      +stage_id() str
      +accept(StageContext, ReviewData) StageOutput
    }

    PlanningStage <|.. DraftStage : implements
    PlanningStage <|.. PlanStage : implements
    PlanningStage <|.. EpicStage : implements
```

## Dependency Order

```mermaid
flowchart LR
    HF["hexagonal-foundation"] --> ESC["event-sourced-core"]
    HF --> PD["projected-documents"]
    HF --> SGOQ["stage-gates-open-questions"]
    HF --> GCAG["guided-cli-agent-guardrails"]
    HF --> SCV["schema-contract-verification"]

    ESC --> PD
    ESC --> SGOQ
    ESC --> GCAG
    ESC --> SCV
    PD --> GCAG
    PD --> SCV
    SGOQ --> GCAG
```

## Event Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant App as PlanningApplication
    participant Runner as StageRunner
    participant Stage as Current Stage
    participant Gate as StageGatePolicy
    participant DB as SQLite Event Store
    participant Proj as Projections

    User->>CLI: enclosure workspace plan next
    CLI->>App: next()
    App->>Runner: advance_current()
    Runner->>Stage: parse_review()
    Runner->>Stage: validate_review()
    Runner->>Gate: check()
    Gate-->>Runner: allow or block
    Runner->>Stage: accept()
    Stage-->>Runner: StageOutput with stable ids
    Runner->>DB: append accepted output events
    DB-->>Proj: notification log
    Proj->>Proj: render next projection with same ids
```

## Candidate Events

```text
PlanCreated
ActivePlanSelected
StageEntered
ProjectionScaffolded
ProjectionRendered
ManualProjectionDriftDetected
OpenQuestionAdded
OpenQuestionAnswered
OpenQuestionClassified
OpenQuestionClassificationConfirmed
StageGateChecked
StageGatePassed
StageGateBlocked
DraftSeedAccepted
PlanContractAccepted
EpicPackageAccepted
StageOutputAccepted
StageAdvanced
RollRequested
RollHalted
StageEnrichmentPreserved
StageEnrichmentOrphaned
```

## Schema Contract Loop

```mermaid
flowchart TD
    Epic["EpicPackage\nstable epic_id"] --> Native["native Mermaid contracts\nflows / uml / tree"]
    Native --> Display["SCHEMAS.md\ndisplay projection"]
    Native --> Implement["agent implementation"]
    Implement --> Actual["actual schemas\nfilesystem + modwire"]
    Actual --> Compare["contract comparison"]
    Compare --> Report["drift report"]
    Report --> Agent["agent repair instruction"]
    Agent --> Implement
```

## Notes

`../STAGES.md` is the specification. These planning-workflow files are the
worked example. The example must keep the six use case slugs stable across
draft, plan, UML, and epic packages so roll can preserve enrichment and schema
verification can trace implementation contracts back to accepted planning data.
