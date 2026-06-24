# Planning Workflow Technical View

## Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DraftSeed
    DraftSeed --> PlanContract: derive plan slots
    PlanContract --> Epics: derive epic slots

    DraftSeed --> DraftSeed: roll starts from seed
    PlanContract --> PlanContract: preserve matched plan enrichment
    Epics --> Epics: preserve matched epic enrichment
    Epics --> [*]: first contract complete
```

## State Procedure

```mermaid
flowchart LR
    Current["Current stage\nselected from events"] --> Intake["Intake\nstage input data objects"]
    Intake --> Derive["Derive slots\ninput id + stage id + variant key"]
    Derive --> Scaffold["Scaffold\nproject docs for review"]
    Scaffold --> Agent["Agent\nupdate current projection"]
    Agent --> Review["User review\napprove or request update"]
    Review --> Gate["Gate\nclassify open questions"]
    Gate --> Accept["Next\naccept stage output"]
    Accept --> Project["Project\nrender markdown and native files"]
    Project --> Current
    Gate --> Blocked["Blocked\nremaining blocking questions"]
    Review --> Halted["Halted\nunresolved roll drift"]
```

## Artifact Projection

```mermaid
flowchart TD
    Commands["workspace plan\nstart / next / agent / roll"] --> App["Planning application\neventsourcing.Application"]
    App --> Store["SQLite event store\n.enclosure/.cache/plans.sqlite"]
    Store --> Aggregate["Plan aggregate\nreconstructed from events"]

    Store --> Draft["DRAFT.md\nstage 1 draft seed"]
    Store --> Plan["PLAN.md\nstage 2 business contract"]
    Store --> RootUML["UML.md\nstage 2 technical contract"]

    Store --> Epics["epics/<epic-slug>/"]
    Epics --> Epic["EPIC.md\nstage 3 epic narrative"]
    Epics --> Stories["USER_STORIES.md\ncurrent epic story placeholders"]
    Epics --> EpicSchemas["SCHEMAS.md\nembedded native projections"]
    Epics --> Flows["flows.mermaid\nprojected flow source"]
    Epics --> Classes["uml.mermaid\nprojected class source"]
    Epics --> Tree["tree.mermaid\nprojected TreeView source"]
```

## Proposed File Tree

```text
.enclosure/
  .cache/
    plans.sqlite
  plans/
    planning-workflow/
      DRAFT.md
      PLAN.md
      UML.md
      epics/
        <epic-name-slug>/
          EPIC.md
          USER_STORIES.md
          SCHEMAS.md
          flows.mermaid
          uml.mermaid
          tree.mermaid
```

## Source Ownership

```mermaid
flowchart LR
    Events["Event stream\ncanonical facts"] --> Aggregate["Plan aggregate\ncurrent state"]
    Events --> Audit["Audit history\nwho changed what and when"]
    Events --> Projectors["Projectors\nderived artifacts"]

    Frontmatter["Frontmatter\nprojected machine-readable view"] --> Drift["Strict sync checks\nprojection vs event state"]
    Markdown["Markdown file\nscaffolded projection"] --> Input["Stage review output\naccepted as events"]
    Input --> Events
    Markdown --> Drift
    Native["Native sources\nflows.mermaid, uml.mermaid, tree.mermaid"] --> Embeds["Markdown embeds\nSCHEMAS.md generated sections"]

    Projectors --> Generated["Generated structure\nsafe to rewrite"]
    Markdown --> Enrichment["Enrichment by derived identity\npreserved across scaffolds"]
    Markdown --> Disposable["Unkeyed edits\nnot authoritative"]
    Drift --> Halt["Unresolved roll drift\nhalts advancement"]
```

## Object Model Sketch

```mermaid
classDiagram
    class PlanningApplication {
      +start()
      +next()
      +agent()
      +roll()
      +get_plan()
    }

    class Plan {
      +str id
      +str title
      +PlanState state
      +bool active
      +current_stage()
      +accept_stage_output()
      +classify_question()
    }

    class PlanningStage {
      +stage_id()
      +intake_type()
      +output_type()
      +derive_slots(input_data)
      +scaffold(input_data)
      +agent_context(input_data)
      +accept(review_data)
    }

    class StageRunner {
      +run_current()
      +advance_current()
      +prepare_agent()
    }

    class RollRunner {
      +start_from_draft()
      +continue_children()
      +halt_on_drift()
    }

    class StageData {
      +str id
      +str stable_identity
      +dict values
    }

    class DerivedSlot {
      +str id
      +str upstream_identity
      +str stage_id
      +str variant_key
    }

    class StageOutput {
      +str next_stage_id
      +list data_objects
    }

    class Enrichment {
      +str slot_id
      +dict values
    }

    class Epic {
      +str id
      +str title
      +str value
      +list stories
    }

    class UserStory {
      +str id
      +str actor
      +str goal
      +str benefit
      +list acceptance_criteria
    }

    class OpenQuestion {
      +str question
      +QuestionStatus status
      +str explanation
      +str decision
      +str reason
      +str revisit_at
    }

    class ArtifactRef {
      +str path
      +str type
      +str source_policy
    }

    class DomainEvent {
      +UUID originator_id
      +int originator_version
      +datetime timestamp
    }

    class Projector {
      +project(event, context)
    }

    class Validator {
      +validate(candidate)
    }

    PlanningApplication --> Plan
    PlanningApplication --> StageRunner
    PlanningApplication --> RollRunner
    Plan "1" --> "*" Epic
    Epic "1" --> "*" UserStory
    Plan "1" --> "*" OpenQuestion
    Plan "1" --> "*" ArtifactRef
    StageRunner --> PlanningStage
    StageRunner --> StageData
    StageRunner --> DerivedSlot
    StageRunner --> StageOutput
    StageRunner --> Enrichment
    RollRunner --> StageRunner
    DomainEvent ..> Plan
    Projector ..> ArtifactRef
    Validator ..> Plan
    Validator ..> Epic
    Validator ..> UserStory
```

## Pattern Fit

```mermaid
flowchart TB
    CLI["CLI command\nstart / next / agent / roll"] --> Command["Command object"]
    Command --> App["PlanningApplication\neventsourcing.Application"]
    App --> Aggregate["Plan aggregate\nstate and transition rules"]
    App --> Runner["Stage runner\ndata in and data out"]
    Runner --> Stage["Current stage\none class in one file"]
    Stage --> Slots["Derived slots\ninput id + stage id + variant key"]
    Slots --> Scaffold["Scaffold policy\nderived IDs and generated sections"]
    App --> Roll["Roll runner\nDRAFT seed through children"]
    Aggregate --> Gates["Stage gates\nopen question classification"]
    Gates --> Confirm["User confirmation\nrequired to unblock"]
    Aggregate --> Specs["Specifications\npolicy and validation"]
    App --> Store["SQLite event store\neventsourcing.sqlite"]
    Store --> Notifications["Notification log\nordered event sequence"]
    Notifications --> Projectors["Projection runners\nmarkdown and diagram views"]
    Projectors --> Sync["Strict sync check\nmust pass before advance"]
    Projectors --> Ports["Ports\nfilesystem, markdown, templates"]
    Ports --> Adapters["Adapters\nCopier, pydantic, jinja2, markdown parser"]
```

## Library Boundary

```mermaid
flowchart LR
    Enclosure["Enclosure planning semantics\nactive plan, lifecycle, drift policy"] --> Planner["workspace.plan module"]

    Planner --> EventSourcing["eventsourcing\naggregates, application, SQLite store, projections"]
    Planner --> Copier["Copier\nprojection templates and updates"]
    Planner --> Pydantic["Pydantic\ntyped event and stage schemas"]
    Planner --> Jinja["Jinja2\nmarkdown rendering"]
    Planner --> Markdown["markdown-it-py\nsection parsing"]
    Planner --> Mermaid["Mermaid CLI\ndiagram validation"]

    Recipes["Existing Enclosure recipes"] -. stay native .-> Enclosure
```

## Event Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant App as PlanningApplication
    participant Plan as Plan Aggregate
    participant DB as SQLite Event Store
    participant Proj as Markdown Projections

    User->>CLI: workspace plan next
    CLI->>App: next()
    App->>Plan: reconstruct from events
    App->>Plan: get current stage
    App->>Plan: derive slots from current input
    App->>Plan: accept matched stage output
    Plan-->>App: stage output events or blocker report
    App->>DB: append event atomically
    DB-->>Proj: notification log
    Proj->>Proj: render DRAFT.md / PLAN.md / UML.md / epics
```

## Candidate Events

```text
PlanCreated
PlanSeededFromDraft
DraftUpdated
RollRequested
RollHalted
StageOutputAccepted
StageSlotsDerived
StageEnrichmentPreserved
StageEnrichmentOrphaned
PlanContractScaffolded
OpenQuestionAdded
OpenQuestionClassified
OpenQuestionClassificationSuggested
OpenQuestionClassificationConfirmed
StageGateChecked
PlanAdvanced
ProjectionRendered
ManualProjectionDriftDetected
EpicAdded
EpicProjectionScaffolded
```

## Notes

The planning module should stay open for extension by adding new events,
aggregate methods, projectors, validators, templates, and transition rules. The
core workflow should not become a single large planner object that knows every
artifact shape.

The event store is the authority. Files are deterministic scaffolded
projections. Stage review output is durable only when `next` accepts it into the
event stream. Generated structure may be rewritten from derived slots, but
enrichment attached to matching derived stable identities must be preserved or
reported as unresolved drift. Unresolved roll drift halts advancement. Roll
always runs forward from `DRAFT.md` seed data to child stages; child projection
shape does not flow back into the draft.

Agents may add questions and set blocking classifications. Non-blocking
classifications require user confirmation before a gate can advance.

## Epic Map

```mermaid
flowchart TD
    Plan["Planning Workflow"] --> Hex["Hexagonal Foundation"]
    Plan --> Core["Event-Sourced Planning Core"]
    Plan --> Docs["Projected Planning Documents"]
    Plan --> CLI["Guided CLI and Agent Guardrails"]
    Plan --> Gates["Stage Gates and Open Questions"]
    Plan --> Contracts["Schema Contract Verification"]

    Hex --> Core
    Hex --> Docs
    Hex --> Gates
    Hex --> CLI
    Hex --> Contracts
    Core --> Docs
    Core --> Gates
    Core --> CLI
    Core --> Contracts
    Docs --> Contracts
    Gates --> CLI
    Docs --> CLI
```

## Epic Dependency Order

```mermaid
flowchart LR
    Hex["0. Hexagonal Foundation\nnext doable"] --> Core["1. Event-Sourced Core"]
    Hex --> Docs["2. Projected Documents"]
    Hex --> Gates["3. Stage Gates"]
    Hex --> CLI["4. Guided CLI"]
    Hex --> Contracts["5. Schema Contract Verification"]
    Core --> Docs
    Core --> Gates["3. Stage Gates"]
    Core --> CLI["4. Guided CLI"]
    Core --> Contracts["5. Schema Contract Verification"]
    Docs --> CLI
    Docs --> Contracts
    Gates --> CLI
```

## Schema Contract Loop

```mermaid
flowchart TD
    Planned["Planned Mermaid contracts\nflows / uml / tree"] --> Implement["Agent implementation"]
    Implement --> Actual["Actual schemas\nfilesystem + modwire"]
    Actual --> Compare["Contract comparison"]
    Compare --> Report["Drift report"]
    Report --> Agent["Agent repair instruction"]
    Agent --> Implement
```

## Flow-to-Implementation Contract

```mermaid
flowchart TD
    Command["command node"] --> Stage["stage: Name\nfile: application/stages/name.py\nclass: Name"]
    Stage --> Slot["derived slot\ninput id + stage id + variant key"]
    Slot --> Domain["domain object or port"]
    Stage --> Event["domain event or projection"]
```

## UML File Annotation Contract

```mermaid
classDiagram
    class PlanStage {
      <<file:application/stages/plan_stage.py>>
      +derive_slots(plan_seed)
      +scaffold(plan_facts)
      +accept(review_data)
    }
```

## Swimlane Flow Convention

```mermaid
flowchart LR
    subgraph commands["Parameterless Commands"]
      Command["command: workspace plan next"]
    end

    subgraph stages["Stages"]
      Stage["stage: PlanStage\nfile: application/stages/plan_stage.py\nclass: PlanStage"]
    end

    subgraph ports["Ports / Domain"]
      Port["port: EventStore"]
    end

    Command --> Stage --> Port
```

Libraries should handle event persistence, parsing, validation, rendering,
formatting, and CLI presentation. Enclosure-specific planning semantics should
remain explicit in the domain and application layers.

Reference: https://eventsourcing.readthedocs.io/en/stable/
