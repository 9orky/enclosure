---
plan_id: planning-workflow
title: Planning Workflow
status: dry-run
stage: draft
active: true
problem: |
  Enclosure keeps implementation code tight and consistent, but planning still
  depends too much on chat context, file state, and agent improvisation.
desired_outcome: |
  Provide a local event-sourced planning workflow that records plan progress as
  durable events and projects those facts into markdown, diagrams, and epic
  packages through a predictable three-stage contract.
key_decisions:
  - Only one plan should be active at a time.
  - The first valid DRAFT.md should seed the event-sourced plan.
  - The authoritative plan state should live in an event-sourced application, not in markdown files.
  - Markdown files and frontmatter should be deterministic projections of the event stream.
  - Use the Python eventsourcing package with SQLite persistence for the planning core.
  - Limit the first predictable workflow to three stages: draft seed, plan contract, and epics.
  - Start from a valid DRAFT.md, then scaffold PLAN.md and UML.md with stable named sections.
  - PLAN.md and UML.md should scaffold epic packages with stable IDs and predictable file names.
  - Users should not need to know internal stage names or step identifiers.
  - The public command surface should be start, next, agent, and roll, without caller-provided params.
  - Every stage should receive typed input data and emit typed output data for the next stage.
  - A stage should be addable as one class in one file implementing the shared stage interface.
  - Repeated scaffolding may add missing IDs and sections, but must preserve existing enrichment.
  - Roll starts from the DRAFT seed and continues across child stages through the same loop.
  - Roll updates must halt advancement when required projected updates remain unresolved.
  - Every workflow state should scaffold, accept agent updates, receive user approval or update requests, and seed the next stage through next.
  - Open questions must be classified before a plan can cross a stage boundary.
  - Blocking open questions should prevent promotion to the next state.
  - Agents may add questions and suggest classifications, but only users can approve non-blocking classifications.
  - Agents can block progress; users must confirm any action that unblocks progress.
  - Keep recipes Enclosure-native for now.
  - Use Copier only for planning projection templates and update experiments.
  - Use libraries for event persistence, parsing, validation, rendering, formatting, and diagram checks.
  - Epic schema bundles should use SCHEMAS.md plus native flows.mermaid, uml.mermaid, and tree.mermaid files.
  - Mermaid schema files are implementation contracts, not documentation-only diagrams.
  - flows.mermaid should define implementation targets with names that map one stage or use case to one class and one file.
  - uml.mermaid classes should use file annotations to declare the relative implementation file for each symbol.
  - flows.mermaid should be swimlaned with commands, closed loop, implementation targets, services/domain/ports, and outputs.
  - tree.mermaid should use the shared Mermaid palette through TreeView theme variables.
  - Planned schema contracts should be compared with implementation schemas derived from modwire after coding.
question_statuses:
  - blocking
  - answered
  - deferred
  - accepted_risk
  - obsolete
candidate_libraries:
  - eventsourcing
  - copier
  - pydantic
  - python-frontmatter
  - jinja2
  - markdown-it-py
  - mermaid-cli
event_store:
  package: eventsourcing
  persistence_module: eventsourcing.sqlite
  database_path: .enclosure/.cache/plans.sqlite
  authority: true
projection_policy:
  markdown_files_are: deterministic scaffolded projections
  regenerate_from: event_store
  user_edits_enter_through: commands
  direct_file_edits: imported_as_events_or_reported_as_drift
  preserve_enrichment_by_stable_id: true
  generated_structure_may_be_rewritten: true
  enriched_content_must_not_be_overwritten_without_drift_report: true
agent_question_policy:
  agent_can_add_questions: true
  agent_can_set_blocking: true
  user_confirms_non_blocking: true
  rule: Agents can create uncertainty; users approve resolving, deferring, accepting, or dismissing it.
epics:
  - id: event-sourced-core
    title: Event-Sourced Planning Core
    folder: epics/event-sourced-core
    ordinal: 1
    status: next_doable
    depends_on: []
  - id: projected-documents
    title: Projected Planning Documents
    folder: epics/projected-documents
    ordinal: 2
    status: blocked_by_dependency
    depends_on:
      - event-sourced-core
  - id: stage-gates-open-questions
    title: Stage Gates and Open Questions
    folder: epics/stage-gates-open-questions
    ordinal: 3
    status: blocked_by_dependency
    depends_on:
      - event-sourced-core
  - id: guided-cli-agent-guardrails
    title: Guided CLI and Agent Guardrails
    folder: epics/guided-cli-agent-guardrails
    ordinal: 4
    status: blocked_by_dependency
    depends_on:
      - event-sourced-core
      - projected-documents
      - stage-gates-open-questions
  - id: schema-contract-verification
    title: Schema Contract Verification
    folder: epics/schema-contract-verification
    ordinal: 5
    status: blocked_by_dependency
    depends_on:
      - event-sourced-core
      - projected-documents
open_questions:
  - question: Should the active-plan lock live in a registry file or inside each plan's frontmatter?
    status: answered
    explanation: Files and frontmatter are now projections, so neither should own concurrency or active-plan authority.
    decision: Neither. Active-plan ownership should be derived from the event-sourced plan aggregate and projected into files.
  - question: How strict should sync be before stage advancement is allowed?
    status: answered
    explanation: Stage advancement may depend on projected files being fresh, but strict sync rules could block useful work too aggressively.
    decision: Use strict sync. The workflow cannot advance while projections are out of sync with the event store.
  - question: Should post-epic automation be automatic or explicit?
    status: obsolete
    explanation: Post-epic automation is outside the first predictable contract because the workflow is intentionally limited to the epics stage.
    decision: Defer post-epic automation out of scope until the three-stage planning contract is implemented and stable.
  - question: Which markdown sections are protected, generated, or freely editable?
    status: answered
    explanation: Projections need clear ownership boundaries so regeneration does not overwrite useful human-authored prose.
    decision: Use deterministic scaffolded projections. The planner owns generated structure, stable IDs, ordering, and section names; enrichment attached to stable IDs is preserved unless drift is reported.
  - question: How should direct manual edits to projected markdown be imported back into the event stream?
    status: answered
    explanation: Users may naturally edit markdown files, but the event store must remain authoritative without silently losing those edits.
    decision: Only accepted stage review output is recorded as events. Edits outside the current stage review surface are not authoritative and may be overwritten by projection sync.
---

# Planning Workflow Draft

## Instructions

Update planning facts through commands that append events. Markdown and
frontmatter are still useful editing and review surfaces, but they are no longer
the ultimate source of truth.

If a user edits a projected file directly, the planner must either import that
edit through a command that records events or report the file as drift.

Projected markdown files are deterministic scaffolded projections. The planner
owns generated structure, stable IDs, ordering, and section names. Human or
agent enrichment attached to those stable IDs should be preserved across
repeated scaffolding unless a roll update reports a conflict or drift.

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
promotions, roll updates, and epic splits should be recorded as durable events
in a local SQLite-backed event store.

Markdown documents, frontmatter, diagrams, and epic packages should be generated
or synchronized projections of that event stream. This avoids making locks and
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
roll updates start from the updated draft seed and continue through child stages
with the same contract. Existing descriptions, rationale, tags, and other
enrichment are preserved by stable ID or reported as unresolved drift.

The existing promoted artifacts should be kept because they represent later
stage projections. They should declare event-store lineage and be refreshed when
new events change their source facts.

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
