# Planning Workflow Draft

## Instructions

Update planning facts through commands that append events. Markdown remains a
useful editing and review surface, but it is no longer the ultimate source of
truth.

If a user edits a projected file directly, the planner must either import that
edit through a command that records events or report the file as drift.

Projected markdown files are deterministic scaffolded projections. The planner
owns generated structure, derived stable identities, ordering, and section
names. Human or agent enrichment attached to those identities should be
preserved across repeated scaffolding unless roll reports a conflict or
drift.

User-editable areas must be explicit stage review surfaces. `workspace plan
next` accepts the current reviewed stage output into events, then strict sync
requires regenerated projections to match the event state.

## Current Intent

The planning module should make Enclosure's planning as consistent as its code
structure. It should create one active planning path, preserve context across
agent sessions, and provide a clean promotion flow from draft seed to plan
contract to epic packages.

The authoritative planning model should be event sourced. Plan creation, draft
updates, stage output acceptance, question classification, stage-gate checks,
promotions, roll requests, and epic splits should be recorded as durable events
in a local SQLite-backed event store.

Markdown documents, diagrams, and epic packages should be generated or
synchronized projections of that event stream. This avoids making locks and
transaction behavior depend on loose filesystem conventions.

The first implementation should use the Python `eventsourcing` package for
aggregates, application command/query methods, SQLite persistence, notification
logs, and projections. Copier remains useful for rendering planning documents,
but it should not own planning state.

Current Enclosure recipes should stay native. Recipes encode architecture
vocabulary and module shape rules that should not be flattened into generic
scaffolding config.

## Workflow Notes

The live dry-run skipped the draft step and created `PLAN.md` and `UML.md`
directly. That remains useful as a test failure: the workflow should always
create or discover the authoritative plan aggregate first, then project
`DRAFT.md`, `PLAN.md`, and schema display documents from recorded events.

The corrected workflow starts when the first valid `DRAFT.md` is accepted as a
seed. That seed deterministically creates the next data set and projected
documents. Later stages use the same loop: the stage receives input objects,
scaffolds projections, the agent updates them, the user approves or asks for
changes, and `next` records output objects that seed the following stage. Later
roll requests start from the updated draft seed and continue through child stages
with the same contract. Existing descriptions, rationale, tags, and other
enrichment are preserved by derived stable identity or reported as unresolved
drift.

`DRAFT.md` does not know what the next stage will scaffold. It only records seed
objects. Each stage owns the transform from its input objects to deterministic
output slots. A stage may produce one output object per input object, a fixed
set of variants per input object, or another cardinality declared by that stage.
The output identity is derived from the upstream stable identity, the stage id,
and the stage-owned variant key. Roll refreshes generated structure in that
direction only: seed to plan data, plan data to epic data, epic data to the
projected tree. Filled content survives when its derived identity still exists;
missing slots are created; orphaned enrichment is reported as drift.

The existing promoted artifacts should be kept because they represent later
stage projections. They should be refreshed when new events change their source
facts.

Open questions should be a formal stage gate. The workflow should not force
every question to be fully answered too early, but it should force every
question to be classified. A plan can advance with answered, deferred,
accepted-risk, or obsolete questions. It cannot advance with blocking questions.
Every open question should include an `explanation` field that says why the
question exists and what uncertainty caused it.

Agents may add open questions and may mark questions as blocking. Agents may
also suggest that a question is answered, deferred, accepted risk, or obsolete,
but the user must confirm any non-blocking classification before the gate can
advance. Agents can create uncertainty; users approve unblocking it.

The current draft gate is unblocked. Uncertainty about post-epic automation is
now outside the first contract because the workflow stops at the epics stage.

## Next Gate

Do not split into epics until this draft, `PLAN.md`, and schema documents agree on the
core direction:

- planning module only;
- recipes left unchanged;
- SQLite event store is authoritative;
- markdown files are projections;
- Copier used as projection support, not as a recipe replacement;
- libraries used at boundaries instead of hand-rolled persistence, parsing, or rendering logic;
- every state uses the same scaffold/agent/user/accept loop;
- the only public subcommands are start, next, agent, and roll;
- stages are data-in/data-out classes behind the command loop;
- roll is forward-only from DRAFT seed to projected tree;
- downstream stage shape is owned by stage implementations, not by DRAFT.md;
- open questions are classified before stage transitions.

Current gate status: ready to split into epics. There are no blocking questions
inside the three-stage contract.

## Epic Split

The epics stage uses five epics:

- 1. Event-Sourced Planning Core
- 2. Projected Planning Documents
- 3. Stage Gates and Open Questions
- 4. Guided CLI and Agent Guardrails
- 5. Schema Contract Verification

The next doable epic is Event-Sourced Planning Core because it has no
dependencies and provides the event authority used by every other epic.

Each epic package owns a schema bundle:

- `tree.mermaid` is the file contract: which files are expected to exist and be edited.
- `uml.mermaid` is the symbol contract: which classes, properties, methods, and relations belong to those files.
- `flows.mermaid` is the flow contract: which commands enter the workflow, which stages or use cases exist, and which ports or domain objects they call.
- `SCHEMAS.md` as the projected display page that embeds the native sources.

Implementation nodes in `flows.mermaid` should follow a parseable naming
convention. For stage-driven planning, a stage is one class in one file:

```text
stage: PlanStage
file: application/stages/plan_stage.py
class: PlanStage
```

This lets the flow contract generate or verify one stage per file and one stage
class per file.

`uml.mermaid` should tag every implementation symbol with its relative file:

```text
class PlanStage {
  <<file:application/stages/plan_stage.py>>
  +scaffold(plan_facts)
  +accept(review_data)
}
```

`flows.mermaid` should be swimlaned with subgraphs so commands/events, use
cases, services/domain/ports, and outputs stay visually aligned. `tree.mermaid`
uses TreeView theme variables for the shared palette because TreeView currently
offers diagram-level theme variables rather than per-node classes.

Epics are the terminal stage of the first predictable planning contract. They
should be independently completable implementation slices with their own
contracts, current story placeholders, and verification path. They do not need
to be independently deployable products; together they still plan the complete
process.

## External Reference

The Python `eventsourcing` package supports event-sourced applications,
application command/query methods, SQLite persistence through
`eventsourcing.sqlite`, notification logs, and projections.

Reference: https://eventsourcing.readthedocs.io/en/stable/
