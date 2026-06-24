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
  - id: run-stage-loop
    title: Run the closed stage loop
    status: candidate
  - id: add-stage-class
    title: Add stages as one class in one file
    status: candidate
  - id: keep-user-stage-agnostic
    title: Keep stage internals out of user workflow
    status: candidate
  - id: roll-from-draft-through-children
    title: Roll from draft through child stages
    status: candidate
  - id: project-schema-page
    title: Project SCHEMAS.md from native Mermaid files
    status: candidate
---

# User Stories

## run-stage-loop

As a user, I want each planning step to behave the same way so that I can review
projected files, ask the agent for updates, and accept the result with `next`.

Acceptance criteria:

- The current stage receives typed input data and scaffolds projected files.
- The agent updates only the current stage projection and context.
- User acceptance records stage output data that seeds the next stage.
- The same loop works for draft, plan, and epic projections.

## add-stage-class

As a developer, I want to add a stage by adding one class in one file so that the
workflow grows without changing the command loop.

Acceptance criteria:

- The shared stage interface declares intake, scaffold, agent context, accept,
  and output behavior.
- Each concrete stage owns the input data it expects.
- Each concrete stage owns the output data it passes to the next stage.
- The stage registry can discover or register a new stage without command
  changes.

## keep-user-stage-agnostic

As a user, I want parameterless commands so that I do not need to know internal
stage names or step identifiers.

Acceptance criteria:

- `start`, `next`, `agent`, and `roll` derive the active plan and current stage.
- Command output explains what changed without requiring stage vocabulary.
- `agent` receives enough bounded context to update the current projection.
- `next` advances only from the current accepted stage output.

## roll-from-draft-through-children

As a user, I want `roll` to refresh the whole planning chain from `DRAFT.md` so
that child projections can be updated consistently.

Acceptance criteria:

- `roll` starts from the draft seed.
- `roll` continues through child stages using the same stage interface.
- Roll output preserves enrichment attached to stable IDs.
- Unresolved conflicts halt with a report instead of overwriting reviewed
  enrichment.

## project-schema-page

As a developer, I want `SCHEMAS.md` generated from native Mermaid files so that
schema diagrams have one native source of truth.

Acceptance criteria:

- `flows.mermaid`, `uml.mermaid`, and `tree.mermaid` remain native projection
  targets.
- `SCHEMAS.md` pastes those native files into the proper markdown sections
  during projection updates.
- Edits to `SCHEMAS.md` generated sections are not treated as schema source
  edits.
