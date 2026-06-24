# User Stories

## Navigation

- Epic: [Projected Planning Documents](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#projected-planning-documents) -> [PLAN.md](../../PLAN.md#projected-documents) -> [UML.md](../../UML.md#slug-identity-contract)
- Siblings: [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## run-stage-loop

As a user, I want each planning step to behave the same way so that I can review
projected files, ask the agent for updates, and accept the result with `next`.

Acceptance criteria:

- The current stage receives typed input data and scaffolds projected files.
- The agent updates only the current stage projection and context.
- User acceptance records stage output data that seeds the next stage.
- The same loop works for draft, plan, and epic projections.

## derive-output-slots

As a developer, I want each stage to derive output slots deterministically so
that roll can refresh generated structure without losing filled content.

Acceptance criteria:

- A stage derives each output slot from upstream stable identity, stage id, and
  stage-owned variant key.
- The stage implementation owns output type, output cardinality, and variant
  rules.
- Generated fields are refreshed during roll.
- Existing enrichment is preserved when the derived slot identity still exists.
- Orphaned enrichment is reported as drift when the upstream identity no longer
  maps to a derived slot.

## add-stage-class

As a developer, I want to add a stage by adding one class in one file so that the
workflow grows without changing the command loop.

Acceptance criteria:

- The shared stage contract is a real abstract base class or interface, not a
  naming convention.
- Every concrete stage explicitly inherits the shared stage contract.
- The shared stage contract declares intake, scaffold, agent context, accept,
  and output behavior.
- Each concrete stage owns the input data it expects.
- Each concrete stage owns the output data it passes to the next stage.
- The stage registry discovers concrete stage subclasses without command,
  use-case, or adapter changes.
- Adding two new stages means adding exactly two new stage files, plus tests and
  docs for those stages.
- Core concrete stages live in the domain layer unless they depend on external
  IO or framework adapters.

## persist-stage-output-as-events

As a developer, I want accepted stage output persisted as true eventsourcing
aggregate events so that the event stream remains the authority.

Acceptance criteria:

- Aggregate-changing events extend the eventsourcing aggregate event base used
  by the planning aggregate.
- Plain dataclass commands or change requests may exist only as application
  input objects; they are not named or treated as domain events.
- Stage acceptance records output object identity, derived slot identity,
  projection paths, and next stage through aggregate events.
- Reconstructing the active plan and current stage uses the event stream, not
  projected markdown files.
- The aggregate defines creation with `class Created(Aggregate.Created)`.
- The aggregate defines stage mutations with nested `Aggregate.Event`
  subclasses such as `StageOutputAccepted`, `ProjectionRecorded`, and
  `StageAdvanced`.
- Aggregate behavior methods call `trigger_event(...)`; application use cases
  persist pending events with `Application.save(plan)`.
- A `domain/events.py` file is not used for plain dataclass change objects; if
  command DTOs are needed, they live in the application layer and are named as
  commands or requests.

## keep-user-stage-agnostic

As a user, I want parameterless commands so that I do not need to know internal
stage names or step identifiers.

Acceptance criteria:

- `start`, `next`, `agent`, and `roll` derive the active plan and current stage.
- Command output explains what changed without requiring stage vocabulary.
- `agent` receives enough bounded context to update the current projection.
- `next` advances only from the current accepted stage output.

## keep-application-layer-abstract

As a developer, I want the application layer to orchestrate through ports and
stage abstractions so that stage details do not leak into command or use-case
logic.

Acceptance criteria:

- Command use cases do not import concrete stage classes.
- Application use cases call only methods declared on the stage base class.
- Projection writes go through a domain port implemented by
  infrastructure.
- Stage-specific review decisions, slot derivation, output construction, and
  transition behavior stay in domain stage implementations.
- Filesystem markdown/native Mermaid IO stays behind infrastructure adapters.
- Optional dynamic stage discovery imports modules and selects non-abstract
  `PlanningStage` subclasses through a domain port; it does not hard-code
  concrete stage names in command or use-case code.

## roll-from-draft-through-children

As a user, I want `roll` to refresh the whole planning chain from `DRAFT.md` so
that child projections can be updated consistently.

Acceptance criteria:

- `roll` starts from the draft seed.
- `roll` continues forward through child stages using the same stage interface.
- `roll` does not read child projection shape back into the draft seed.
- Roll output preserves enrichment attached to derived stable identities.
- Unresolved conflicts halt with a report instead of overwriting reviewed
  enrichment.

## project-schema-page

As a developer, I want `SCHEMAS.md` generated from native Mermaid files so that
schema diagrams have one native source of truth.

Acceptance criteria:

- `flows.mermaid`, `uml.mermaid`, and `tree.mermaid` remain native projection
  targets.
- The owning concrete stage declares the file model for every projected native
  Mermaid file and markdown file it emits.
- `SCHEMAS.md` pastes those native files into the proper markdown sections
  during projection updates.
- Edits to `SCHEMAS.md` generated sections are not treated as schema source
  edits.
