---
plan_id: planning-workflow
epic_id: projected-documents
title: Projected Planning Documents Stories
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
stories:
  - id: render-plan-documents
    title: Render planning documents from events
    status: candidate
  - id: preserve-enrichment-during-scaffold
    title: Preserve enrichment during repeated scaffolding
    status: candidate
  - id: halt-unresolved-roll-update
    title: Halt unresolved roll updates
    status: candidate
  - id: import-input-blocks
    title: Import marked input blocks
    status: candidate
  - id: enforce-strict-sync
    title: Enforce strict projection sync
    status: candidate
---

# User Stories

## render-plan-documents

As a user, I want planning documents rendered from event state so that files are
readable views of the authoritative plan.

Acceptance criteria:

- The planner renders draft seed, plan contract, UML contract, and epic package
  documents.
- Projected files declare source and sync policy.
- Projection rendering is deterministic.

## preserve-enrichment-during-scaffold

As a user, I want repeated scaffolding to preserve descriptions and tags already
attached to stable IDs so that roll updates can safely refresh structure.

Acceptance criteria:

- Generated IDs, slugs, ordering, and section names can be refreshed.
- Existing enrichment attached to stable IDs is preserved.
- Removed or renamed IDs create a drift report instead of silent overwrite.

## halt-unresolved-roll-update

As the planner, I want unresolved roll updates to halt advancement so that
agents cannot advance from mismatched planning documents.

Acceptance criteria:

- Roll update reports required changes it cannot reconcile automatically.
- Advancement fails while required roll updates are unresolved.
- Resolving the drift and regenerating projections restores advancement.

## import-input-blocks

As a user, I want to type answers inside marked input blocks so that VS Code
remains a natural planning surface.

Acceptance criteria:

- `workspace plan next` imports marked blocks.
- Imports append events.
- Edits outside marked blocks are ignored or reported as drift.

## enforce-strict-sync

As the planner, I want to block advancement when projections are stale so that
agents and users do not make decisions from mismatched files.

Acceptance criteria:

- Status reports projection sync state.
- Advancement fails if projections do not match event state.
- Regeneration restores projection sync.
