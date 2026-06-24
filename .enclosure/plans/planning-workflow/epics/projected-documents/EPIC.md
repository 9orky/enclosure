# Projected Planning Documents

## Navigation

- Draft source: [Projected Planning Documents](../../DRAFT.md#projected-planning-documents)
- Plan source: [projected-documents](../../PLAN.md#projected-documents)
- Technical id contract: [UML.md](../../UML.md#slug-identity-contract)
- Epic artifacts: [USER_STORIES.md](USER_STORIES.md), [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## Source Chain

```text
draft_use_case_id: projected-documents
plan_item_id: projected-documents
epic_id: projected-documents
```

This epic reuses the draft use case and plan item for `projected-documents`.
The slug stays stable because no split rule creates variants for this example.

## Reused Plan Data

Intent: render event-sourced planning facts into deterministic markdown and
native schema files while preserving reviewed enrichment by stable identity.

Planned outcome: the planner can scaffold, parse, validate, accept, and rerender
stage projections without losing enrichment attached to derived stable
identities.

Accepted constraints:

- `DRAFT.md`, `PLAN.md`, `UML.md`, and epic packages are projections.
- Each stage owns its input type, output type, output cardinality, and slots.
- `SCHEMAS.md` is display-only; native Mermaid files are schema sources.
- Stage behavior is expressed through real Python base classes and ports,
  not by convention-only class names.
- Aggregate mutations are recorded by eventsourcing-native aggregate events;
  plain dataclass command/change objects are not domain events.
- The implementation follows the `eventsourcing` package boilerplate:
  aggregate roots subclass `eventsourcing.domain.Aggregate`, creation events
  subclass `Aggregate.Created`, mutation events subclass `Aggregate.Event`,
  aggregate methods call `trigger_event(...)`, and the application persists the
  aggregate with `Application.save(...)`.

## Value

This epic preserves the comfortable markdown workflow while keeping the event
store authoritative. Users do not need to know stage names or internal step
labels; they see projected files, ask the agent to update them, and accept the
current result when it is good enough to seed the next set of data objects.

## Outcome

Planning artifacts are scaffolded by the current stage from typed input data.
The agent updates the scaffolded projection, the user approves or asks for more
updates, and `next` accepts the current stage output as the seed for the next
stage. Every stage follows the same data-in/data-out contract, so adding a stage
means adding one concrete stage class in one new stage file. Command handlers,
application use cases, projection adapters, and existing stage files are
unchanged.

`roll` is forward-only. It starts from `DRAFT.md` seed objects, derives output
slots through each child stage, refreshes generated structure, and preserves
filled content by derived stable identity. The draft seed does not know the
child projection shape; each stage implementation owns its own output object
type, cardinality, and variant keys.

The domain layer owns the planning workflow vocabulary. `PlanningStage`,
`StageInput`, `StageOutput`, `DerivedSlot`, `ReviewData`, `ValidationResult`,
`StageRegistry`, the core stage implementations, and the event-sourced `Plan`
aggregate are domain concepts. Core stages such as draft, plan, and epics are
not infrastructure just because they are pluggable; they are pure planning
behavior unless they depend on filesystem, network, templates, or other
technical adapters.

The application layer owns use-case orchestration only. It loads and saves the
event-sourced aggregate, asks the domain registry for the current stage, calls
methods declared by the domain `PlanningStage` and `StageFileContract`
contracts, and writes returned projection artifacts through domain ports.
Application code does not know
whether a stage performs question-and-answer loops, advances directly, blocks
on validation, or emits drift; that decision is returned by the domain stage
result.

The infrastructure layer owns technical details. Filesystem projection storage,
content hashing, markdown/native Mermaid IO, and optional dynamic stage-module
discovery implement domain ports. Infrastructure may discover or load
stage classes, but it must not own stage progression rules.

The event-sourcing implementation is not a custom event bus. The planning
aggregate exposes behavior methods such as `accept_stage_output(...)`,
`record_projection(...)`, `advance_stage(...)`, and `request_roll(...)`. Each
method triggers a nested aggregate event class, for example
`Plan.StageOutputAccepted(Aggregate.Event)`, and the application saves the
changed aggregate. Application command objects may exist to carry input into a
use case, but they are not named events and they do not live in a domain
`events.py` file.

## Navigation

Previous dependencies:

- Hexagonal Foundation
- Event-Sourced Planning Core

Next dependent epic:

- Guided CLI and Agent Guardrails
- Schema Contract Verification

## Contract Role

`tree.mermaid` defines projection and stage files. `uml.mermaid` defines the
domain stage identity interface, stage file contract, schema contract, concrete
domain stage subclasses, event-sourced aggregate, application use cases, domain
ports, infrastructure adapters, and schema display projection. `flows.mermaid`
defines the closed stage loop and the parameterless command entry points that
drive it.

## Boundaries

This epic does not own CLI parsing or stage gate policy. It does not replace
the event-sourced core event model; accepted stage output is persisted through
eventsourcing-native aggregate events owned by the planning aggregate. It owns
how event-sourced facts become stage input data, projected markdown, native
Mermaid files, `SCHEMAS.md`, and stage output data. Its stage and projection
ports follow the shared hexagonal shape.

## Acceptance Criteria

- `PlanningStage` is a real abstract base class or interface in the domain
  layer; every concrete stage explicitly inherits it.
- `StageFileContract` is a real abstract base class in the domain layer; every
  concrete stage explicitly inherits it.
- Every stage lives as one concrete class in one stage file.
- Every stage implements its own file model declaration; projected stage files
  are never inferred by a generic projector from prose or folder naming alone.
- Adding two new stages requires two new concrete stage files and no changes to
  command handlers, application use cases, existing stages, or projection
  adapters.
- Every stage declares the data objects it accepts and the data objects it
  outputs.
- Every stage derives output slots from upstream stable identity, stage id, and
  stage-owned variant keys.
- The domain stage registry receives or resolves `PlanningStage` instances
  without a switch statement or per-stage edit in command/use-case code.
- Application use cases depend on domain stage contracts and domain ports,
  not on concrete stage classes.
- Infrastructure implements filesystem projection and optional stage discovery
  ports; it does not own stage behavior.
- Accepted stage output is saved through eventsourcing aggregate events; there
  is no `domain/events.py` file for plain dataclass event substitutes.
- Domain event classes are nested on the aggregate or otherwise subclass the
  exact eventsourcing aggregate-event base required by the aggregate.
- Application use cases call aggregate behavior methods and then
  `Application.save(plan)`; they do not directly append dictionaries, dataclass
  changes, or projection records to persistence.
- Replaying uses the eventsourcing repository and notification log, not a
  custom event list.
- `start`, `next`, `agent`, and `roll` work as parameterless subcommands from
  the caller's point of view.
- `next` accepts the current reviewed projection and seeds the next stage from
  the current stage output.
- `agent` receives bounded current-stage data without requiring the user to know
  internal stage names.
- `roll` starts from the `DRAFT.md` seed and continues across child stages using
  the same stage contract.
- `roll` never pushes downstream projection shape back into `DRAFT.md`.
- `DRAFT.md`, `PLAN.md`, `UML.md`, and epic packages are deterministic stage
  projections.
- Enrichment attached to derived stable identities is preserved across repeated
  scaffolds.
- Removed or renamed upstream identities orphan downstream enrichment unless an
  explicit alias or drift resolution reconnects it.
- Native files such as `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`
  remain projection targets modeled by the owning stage.
- `SCHEMAS.md` is a display projection generated by pasting the native Mermaid
  sources into the proper markdown sections.
