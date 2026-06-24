---
plan_id: planning-workflow
title: Planning Workflow Technical View
status: dry-run
stage: plan-contract
source: event_store
generated_from: eventsourcing projection
sync_policy: projection
active: true
---

# Planning Workflow Technical View

## Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DraftSeed
    DraftSeed --> PlanContract: scaffold PLAN.md and UML.md
    PlanContract --> Epics: scaffold epic packages

    DraftSeed --> DraftSeed: roll updated DRAFT.md
    PlanContract --> PlanContract: roll updated plan contract
    Epics --> Epics: roll updated epic projections
    Epics --> [*]: first contract complete
```

## State Procedure

```mermaid
flowchart LR
    Enter["Enter\ncreate or reconstruct aggregate"] --> Edit["Edit\ncommands append events"]
    Edit --> Roll["Roll update\nimport marked blocks and detect drift"]
    Roll --> Scaffold["Scaffold\nstable IDs, sections, files"]
    Scaffold --> Check["Check\nschema, lineage, strict sync, required fields"]
    Check --> Gate["Gate\nclassify open questions"]
    Gate --> Advance["Advance\nappend transition event"]
    Advance --> Project["Project\nrender markdown and native files"]
    Gate --> Blocked["Blocked\nremaining blocking questions"]
    Check --> Halted["Halted\nunresolved roll updates"]
```

## Artifact Projection

```mermaid
flowchart TD
    Commands["workspace plan commands"] --> App["Planning application\neventsourcing.Application"]
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
    Markdown["Markdown file\nscaffolded projection"] --> Input["Marked input blocks\nimported as events"]
    Input --> Events
    Markdown --> Drift
    Native["Native sources\nflows.mermaid, uml.mermaid, tree.mermaid"] --> Embeds["Markdown embeds\nSCHEMAS.md generated sections"]

    Projectors --> Generated["Generated structure\nsafe to rewrite"]
    Markdown --> Enrichment["Enrichment by stable ID\npreserved across scaffolds"]
    Markdown --> Disposable["Unkeyed edits\nnot authoritative"]
    Drift --> Halt["Unresolved roll update\nhalts advancement"]
```

## Object Model Sketch

```mermaid
classDiagram
    class PlanningApplication {
      +create_plan()
      +seed_from_draft()
      +roll_update()
      +scaffold_plan_contract()
      +scaffold_epics()
      +classify_question()
      +advance_plan()
      +get_plan()
    }

    class Plan {
      +str id
      +str title
      +PlanState state
      +bool active
      +seed_from_draft()
      +roll_update()
      +scaffold_next_stage()
      +advance()
      +classify_question()
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

    class Scaffolder {
      +scaffold_draft_seed()
      +scaffold_plan_contract()
      +scaffold_epics()
    }

    class RollUpdate {
      +import_marked_blocks()
      +preserve_enrichment()
      +report_unresolved_changes()
    }

    class InputBlockImporter {
      +extract_answers(path)
      +import_answers()
    }

    class Validator {
      +validate(candidate)
    }

    PlanningApplication --> Plan
    Plan "1" --> "*" Epic
    Epic "1" --> "*" UserStory
    Plan "1" --> "*" OpenQuestion
    Plan "1" --> "*" ArtifactRef
    DomainEvent ..> Plan
    Projector ..> ArtifactRef
    Scaffolder ..> Plan
    RollUpdate ..> PlanningApplication
    InputBlockImporter ..> PlanningApplication
    Validator ..> Plan
    Validator ..> Epic
    Validator ..> UserStory
```

## Pattern Fit

```mermaid
flowchart TB
    CLI["CLI command\nworkspace plan ..."] --> Command["Command object"]
    Command --> App["PlanningApplication\neventsourcing.Application"]
    App --> Aggregate["Plan aggregate\nstate and transition rules"]
    Aggregate --> Scaffold["Scaffold policy\nstable IDs and generated sections"]
    Aggregate --> Roll["Roll update policy\npreserve enrichment or halt"]
    Aggregate --> Gates["Stage gates\nopen question classification"]
    Gates --> Confirm["User confirmation\nrequired to unblock"]
    Aggregate --> Specs["Specifications\npolicy and validation"]
    App --> Store["SQLite event store\neventsourcing.sqlite"]
    Store --> Notifications["Notification log\nordered event sequence"]
    Notifications --> Projectors["Projection runners\nmarkdown and diagram views"]
    Projectors --> Sync["Strict sync check\nmust pass before advance"]
    Projectors --> Ports["Ports\nfilesystem, frontmatter, markdown, templates"]
    Ports --> Adapters["Adapters\nCopier, pydantic, frontmatter, jinja2, markdown parser"]
```

## Library Boundary

```mermaid
flowchart LR
    Enclosure["Enclosure planning semantics\nactive plan, lifecycle, drift policy"] --> Planner["workspace.plan module"]

    Planner --> EventSourcing["eventsourcing\naggregates, application, SQLite store, projections"]
    Planner --> Copier["Copier\nprojection templates and updates"]
    Planner --> Pydantic["Pydantic\nfrontmatter schemas"]
    Planner --> Frontmatter["python-frontmatter\nmetadata/body split"]
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
    CLI->>App: roll_update(plan_id)
    App->>Plan: reconstruct from events
    Plan->>Plan: import input and scaffold next stage
    Plan->>Plan: enforce roll update and gate
    Plan-->>App: new domain events or unresolved update report
    App->>DB: append event atomically
    DB-->>Proj: notification log
    Proj->>Proj: render DRAFT.md / PLAN.md / UML.md / epics
```

## Candidate Events

```text
PlanCreated
PlanSeededFromDraft
DraftUpdated
DraftInputBlockImported
RollUpdateRequested
RollUpdateHalted
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
projections. Direct file edits are durable only when they occur inside marked
input blocks and are imported as events. Generated structure may be rewritten,
but enrichment attached to stable IDs must be preserved or reported as
unresolved drift. Unresolved roll updates halt advancement.

Agents may add questions and set blocking classifications. Non-blocking
classifications require user confirmation before a gate can advance.

## Epic Map

```mermaid
flowchart TD
    Plan["Planning Workflow"] --> Core["Event-Sourced Planning Core"]
    Plan --> Docs["Projected Planning Documents"]
    Plan --> CLI["Guided CLI and Agent Guardrails"]
    Plan --> Gates["Stage Gates and Open Questions"]
    Plan --> Contracts["Schema Contract Verification"]

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
    Core["1. Event-Sourced Core\nnext doable"] --> Docs["2. Projected Documents"]
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

## Flow-to-Use-Case Contract

```mermaid
flowchart TD
    Command["command node"] --> UseCase["usecase: Name\nfile: application/use_cases/name.py\nclass: Name"]
    UseCase --> Domain["domain object or port"]
    UseCase --> Event["domain event or projection"]
```

## UML File Annotation Contract

```mermaid
classDiagram
    class ImportInputBlocks {
      <<file:application/use_cases/import_input_blocks.py>>
      +execute(plan_id)
    }
```

## Swimlane Flow Convention

```mermaid
flowchart LR
    subgraph commands["Commands / Events"]
      Command["command: workspace plan next"]
    end

    subgraph use_cases["Use Cases"]
      UseCase["usecase: ImportInputBlocks\nfile: application/use_cases/import_input_blocks.py\nclass: ImportInputBlocks"]
    end

    subgraph ports["Ports / Domain"]
      Port["port: EventStore"]
    end

    Command --> UseCase --> Port
```

Libraries should handle event persistence, parsing, validation, rendering,
formatting, and CLI presentation. Enclosure-specific planning semantics should
remain explicit in the domain and application layers.

Reference: https://eventsourcing.readthedocs.io/en/stable/
