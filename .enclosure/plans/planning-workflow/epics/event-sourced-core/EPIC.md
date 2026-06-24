---
plan_id: planning-workflow
epic_id: event-sourced-core
title: Event-Sourced Planning Core
ordinal: 1
status: dry-run
readiness: next_doable
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
depends_on: []
blocks:
  - projected-documents
  - guided-cli-agent-guardrails
  - stage-gates-open-questions
  - schema-contract-verification
owns:
  - Plan aggregate
  - Planning application command/query boundary
  - SQLite event persistence
  - Domain events
  - Reconstructed current state
---

# Event-Sourced Planning Core

## Value

This epic gives the planning module a reliable authority model. Instead of
treating markdown files as the database, plan facts are appended as durable
events and reconstructed into current state when commands run.

## Outcome

The workspace can create one active plan, record plan changes in SQLite, and
reconstruct the current plan state through the planning application.

## Navigation

Previous epic: none.

Next dependent epics:

- Projected Planning Documents
- Guided CLI and Agent Guardrails
- Stage Gates and Open Questions
- Schema Contract Verification

## Contract Role

`tree.mermaid` defines the event core files. `uml.mermaid` defines the aggregate,
application, event, and use-case symbols. `flows.mermaid` defines the
event-sourced application use cases.

## Boundaries

This epic does not own markdown rendering, CLI interaction details, or epic
projection formats. It owns the source of truth that those layers depend on.

## Acceptance Criteria

- Plan creation appends durable events.
- Only one active plan can exist.
- Current plan state can be reconstructed from events.
- Event append behavior is atomic through SQLite persistence.
- Downstream projectors can consume ordered plan events.
