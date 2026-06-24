# Planning Workflow

## Purpose

Enclosure keeps implementation structure tight and consistent, but planning still
depends too much on chat context, file state, and agent improvisation. This plan
introduces a local event-sourced planning workflow that records planning facts as
durable events and projects them into readable markdown artifacts.

The goal is to make planning explicit, inspectable, repeatable, and enforceable
without making markdown files carry transaction and locking responsibilities.
The first predictable contract intentionally stops at the epics stage.

## Business Value

This workflow should help Enclosure users move from an initial idea to
implementation-ready epics with less ambiguity. It creates one visible planning
path, keeps decision records close to the codebase, and gives agents a stable
source of truth instead of reconstructing intent from conversation history.

The stable source of truth should be a local SQLite-backed event-sourced
planning subsystem. The documents remain valuable because they are readable,
reviewable, and familiar, but canonical facts should be recorded as events and
projected back into files.

Expected value:

- Reduce confusion caused by multiple competing plans.
- Preserve planning context across agent sessions.
- Give users editable planning documents without making files the authority.
- Create a clean promotion path from draft seed to plan contract to epic
  packages.
- Make drift between projected files and event-sourced facts detectable.
- Preserve a transactional history of planning decisions and stage transitions.
- Improve repeatability by generating consistent plan artifacts and epic
  packages from typed events and projections.

## Scope

The workflow starts with a single active event-sourced plan aggregate and
projects it into a three-stage planning contract:

- Stage 1, draft seed: the first valid `DRAFT.md` records initial user and
  agent intent.
- Stage 2, plan contract: `PLAN.md` explains business purpose and value, while
  `UML.md` records the technical contract.
- Stage 3, epics: epic folders contain projected epic-level intent, current
  story placeholders, and Mermaid schema contracts.

Users should not need to know these stage names while operating the workflow.
Commands derive the active plan and current stage from event state. Each stage
receives a list of typed data objects, scaffolds reviewable projections, accepts
agent and user updates, and emits the data objects that seed the next stage.
The upstream data does not describe what the next projection will look like.
Projection shape, output object type, and output cardinality are owned by the
stage implementation.

The first implementation should use the Python `eventsourcing` package with
SQLite persistence for the planning core. Plan commands append domain events;
queries reconstruct the current plan state; stage projections render markdown,
diagrams, and epic packages.

## Tooling Position

`eventsourcing` should own the application/event-store mechanics. Copier should
be considered a projection renderer for markdown artifact templates, not the
planning authority.

Recipes should remain Enclosure-native because they carry architecture-specific
meaning: archetypes, ladders, slots, target semantics, and module shape
vocabulary. Copier can be evaluated as a rendering/update backend for planning
documents first, then considered later as an implementation detail behind
selected recipes if that proves useful.

## Non-Goals

This plan does not define the full implementation of the planning module yet.
It also does not attempt to replace issue trackers, sprint planning, or external
project management systems. The first useful version should stay local,
markdown-readable, and aligned with Enclosure's existing filesystem workflow.
Post-epic automation is intentionally out of scope for the first contract.

## Operating Principles

Only one plan should be active at a time. Active-plan ownership should be
enforced by the event-sourced application. The filesystem can expose the active
plan through projected files, but it should not be the locking mechanism.

Structured planning data belongs in events. Markdown projections may contain
readable explanation and current-stage review surfaces. Generated structure,
derived stable identities, section names, and ordering are owned by the planning
module. Enrichment attached to derived stable identities must survive repeated
scaffolding unless roll reports unresolved drift.

Projection source and sync policy belong to the planner implementation.
Regeneration may rewrite generated structure, but it must preserve enrichment
attached to derived stable identities or report unresolved drift. User input is
durable only after it is accepted as current-stage output into the event store.

Native source files should own native formats as projections. For example,
`flows.mermaid`, `uml.mermaid`, and `tree.mermaid` should remain the native
Mermaid sources consumed by `SCHEMAS.md`. These Mermaid files are implementation
contracts, not documentation-only diagrams. The fact that each contract exists,
belongs to an epic, and was approved at a particular stage belongs to the event
stream.

Every workflow state should have the same basic closed loop: scaffold the
current stage from its input data, let the agent update the projection, let the
user approve or request changes, then accept the stage output with `next`. This
keeps the workflow predictable without exposing internal stage names to users.

The public command surface should be only `start`, `next`, `agent`, and `roll`,
with no command parameters required by the caller. `roll` is special because it
starts from the `DRAFT.md` seed and continues across child stages through the
same stage contract.

Roll is a forward-only recomputation from seed to tree. `DRAFT.md` owns only the
seed data objects. A downstream stage derives deterministic output slots from
the stable identity of its input objects plus its own stage and variant rules.
For example, five seed objects may produce five plan objects, or five declared
variants, because that cardinality is known by the stage implementation. During
roll, generated fields are refreshed, missing derived slots are created, and
accepted enrichment is preserved by derived stable identity. Removed or renamed
upstream identities orphan downstream enrichment unless an explicit alias or
drift resolution reconnects it. Downstream projection shape is never pushed back
into `DRAFT.md`.

Projection sync should be strict. The workflow cannot advance while projected
files are out of sync with the event store.

Open questions should be treated as stage-gate inputs. The workflow should not
force premature certainty, but it should prevent silent uncertainty. Before a
plan crosses a stage boundary, every open question must be classified as
answered, deferred, accepted risk, obsolete, or blocking. Blocking questions stop
promotion. Every open question should also explain why it was asked and what
confusion or uncertainty caused it.

Agents may add questions and may mark questions as blocking. They may propose
non-blocking classifications, but users must confirm anything that unblocks a
stage gate. This keeps the agent useful without letting it silently approve its
own uncertainty.

## Epic Split

The first implementation should be split into six epics:

- 0. Hexagonal Foundation: own the shared port, adapter, and dependency-shape
  interfaces that keep the planning module's hexagonal structure consistent.
- 1. Event-Sourced Planning Core: own the event-sourced aggregate, SQLite-backed
  application, event definitions, and reconstructed plan state.
- 2. Projected Planning Documents: own deterministic stage projections,
  stage intake/output data, enrichment preservation, `SCHEMAS.md` display
  projection, roll continuity, and document rendering.
- 3. Stage Gates and Open Questions: own stage procedures, gate evaluation,
  question classification, and user-confirmed unblocking.
- 4. Guided CLI and Agent Guardrails: own the parameterless `workspace plan`
  command loop, start/next/agent/roll guidance, and safe command boundaries.
- 5. Schema Contract Verification: own comparison between planned Mermaid
  contracts and actual implementation schemas derived from modwire.

## Epic Navigation

Next doable epic:

- [Hexagonal Foundation](epics/hexagonal-foundation/EPIC.md)

Epic order:

| Ordinal | Epic | Status | Depends On |
| --- | --- | --- | --- |
| 0 | [Hexagonal Foundation](epics/hexagonal-foundation/EPIC.md) | next doable | none |
| 1 | [Event-Sourced Planning Core](epics/event-sourced-core/EPIC.md) | blocked by dependency | hexagonal-foundation |
| 2 | [Projected Planning Documents](epics/projected-documents/EPIC.md) | blocked by dependency | hexagonal-foundation, event-sourced-core |
| 3 | [Stage Gates and Open Questions](epics/stage-gates-open-questions/EPIC.md) | blocked by dependency | hexagonal-foundation, event-sourced-core |
| 4 | [Guided CLI and Agent Guardrails](epics/guided-cli-agent-guardrails/EPIC.md) | blocked by dependency | hexagonal-foundation, event-sourced-core, projected-documents, stage-gates-open-questions |
| 5 | [Schema Contract Verification](epics/schema-contract-verification/EPIC.md) | blocked by dependency | hexagonal-foundation, event-sourced-core, projected-documents |

The order is a projection of epic dependencies, not a hand-maintained preference
list. When an epic is completed, the next doable epic should be recalculated
from dependency status.

## Epic Package Shape

Each epic folder should be internally navigable and carry its own development
schema bundle:

```text
EPIC.md
USER_STORIES.md
SCHEMAS.md
flows.mermaid
uml.mermaid
tree.mermaid
```

`SCHEMAS.md` is only a display projection. The native Mermaid files are the
sources, and projection updates paste their content into the proper
`SCHEMAS.md` sections. `flows.mermaid` should use a flowchart for the primary
flow contract because flowchart nodes are easier to parse into implementation
targets.
`uml.mermaid` should use class diagrams. `tree.mermaid` should use Mermaid
TreeView syntax. Sequence diagrams can be added later as secondary views, but
they should not replace the parseable flow contract.

The native Mermaid files are also contracts:

- `tree.mermaid` defines the expected files for the epic.
- `uml.mermaid` defines the expected symbols, relationships, properties, and
  methods.
- `flows.mermaid` defines the expected command entry points, stage loop,
  implementation targets, and domain or port calls they orchestrate.

After implementation, Enclosure should derive actual schemas from the filesystem
and modwire, compare them with the planned contracts, and report drift back to
the agent.

Implementation nodes in `flows.mermaid` should be named so they can be
transformed into implementation targets. For a stage-driven workflow, a stage is
one class in one file implementing the shared stage interface:

```text
stage: PlanStage
file: application/stages/plan_stage.py
class: PlanStage
```

The intended stage implementation rule is one stage per file and one stage class
per file. That closes the application-layer gap: agents no longer invent the
stage layout from scratch.

Every implementation class in `uml.mermaid` should carry a file annotation:

```text
class PlanStage {
  <<file:application/stages/plan_stage.py>>
  +scaffold(plan_facts)
  +accept(review_data)
}
```

The annotation is the symbol-to-file contract. Modwire-derived actual symbols
can be compared against this tag to detect misplaced or missing implementations.

`flows.mermaid` should use swimlane-style subgraphs:

- parameterless commands;
- the closed stage loop;
- stage classes, services, domain objects, and ports;
- outputs such as projections, events, guidance, gates, and reports.

`tree.mermaid` should use the shared Mermaid palette through TreeView theme
variables. TreeView has a smaller styling surface than flowcharts, so palette
normalization is diagram-level rather than per-node.

An epic is the terminal artifact of the first predictable planning contract. It
is an independently completable implementation slice with its own contracts,
current story placeholders, and verification path. It does not need to be
independently deployable as a standalone product. The full plan still describes
the complete process.

## Success Criteria

- A user can create one active plan through the workspace CLI.
- Planning commands are recorded as durable events in SQLite.
- A valid `DRAFT.md` can seed the event-sourced plan.
- Draft facts deterministically scaffold `PLAN.md` and `UML.md`.
- `PLAN.md` and `UML.md` deterministically scaffold epic packages.
- Users can run the loop with only `start`, `next`, `agent`, and `roll`.
- New stages can be added as one class in one file implementing the stage
  interface.
- Roll always recomputes forward from seed data to projected tree.
- Stage output slots are derived deterministically from upstream stable
  identities and stage-owned variant rules.
- Repeated scaffolding preserves enrichment attached to derived stable
  identities.
- Mermaid contracts can be compared with actual implementation structure.
- Drift between projected files and event-sourced state can be detected and
  repaired or imported.
- User review output can be accepted as stage output events.
- Stage advancement is blocked when projections are not strictly synchronized.
- Roll halts advancement when required drift remains unresolved.
- New artifact types can be added without rewriting the whole planner.
- Open questions cannot be silently carried across stage boundaries.
- Agents cannot silently unblock questions they introduced or reclassified.

## Open Questions

- How much of Copier's update model should be exposed directly to users?

## External Reference

The selected event sourcing package is documented at
https://eventsourcing.readthedocs.io/en/stable/. Its documentation covers
event-sourced applications, SQLite persistence with `eventsourcing.sqlite`,
notification logs, and projections.
