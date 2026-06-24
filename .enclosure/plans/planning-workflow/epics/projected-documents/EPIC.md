---
plan_id: planning-workflow
epic_id: projected-documents
title: Projected Planning Documents
ordinal: 2
status: dry-run
readiness: blocked_by_dependency
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
depends_on:
  - event-sourced-core
blocks:
  - guided-cli-agent-guardrails
  - schema-contract-verification
owns:
  - Deterministic scaffolded projections
  - Marked input blocks
  - Stable ID preservation
  - Strict projection sync
  - Roll update halt reports
  - Copier-backed rendering experiments
---

# Projected Planning Documents

## Value

This epic preserves the comfortable markdown workflow while keeping the event
store authoritative. Users can read and answer inside projected files, while the
planner imports marked input blocks into durable events.

## Outcome

Planning artifacts are scaffolded from event state, strict sync prevents stale
projections from advancing, and marked input blocks provide a controlled editing
surface. Repeated scaffolding preserves enrichment attached to stable IDs and
halts when a roll update requires unresolved human or agent decisions.

## Navigation

Previous dependency:

- Event-Sourced Planning Core

Next dependent epic:

- Guided CLI and Agent Guardrails
- Schema Contract Verification

## Contract Role

`tree.mermaid` defines projection/import files. `uml.mermaid` defines renderer,
importer, scaffolder, roll-update, sync checker, and use-case symbols.
`flows.mermaid` defines the projection, import, scaffold, roll-update, schema
rendering, and strict-sync use cases.

## Boundaries

This epic does not own the domain event model or stage gate policy. It owns how
event-sourced facts appear as markdown, frontmatter, diagrams, and file trees.

## Acceptance Criteria

- The first valid `DRAFT.md` can seed the event-sourced plan.
- `DRAFT.md`, `PLAN.md`, `UML.md`, and epic packages are deterministic
  scaffolded projections.
- Marked input blocks can be imported into events.
- Enrichment attached to stable IDs is preserved across repeated scaffolds.
- Edits outside marked input blocks are not authoritative unless imported.
- Strict sync detects stale or divergent projections.
- Roll updates halt when generated structure and preserved enrichment cannot be
  reconciled automatically.
- Native files such as `flows.mermaid`, `uml.mermaid`, and `tree.mermaid`
  remain projection targets.
