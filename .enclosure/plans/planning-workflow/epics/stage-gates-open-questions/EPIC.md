---
plan_id: planning-workflow
epic_id: stage-gates-open-questions
title: Stage Gates and Open Questions
ordinal: 3
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
owns:
  - Stage procedure
  - Gate evaluation
  - Open question model
  - User-confirmed unblocking
---

# Stage Gates and Open Questions

## Value

This epic prevents plans from advancing while important uncertainty is silently
ignored. It makes open questions first-class, explained, classified, and enforced
by stage gates.

## Outcome

Every stage has a consistent enter, edit, import, check, gate, advance, and
project procedure. Questions can block progress, and agents cannot silently
unblock their own uncertainty.

## Navigation

Previous dependency:

- Event-Sourced Planning Core

Next dependent epic:

- Guided CLI and Agent Guardrails

## Contract Role

`tree.mermaid` defines gate and question files. `uml.mermaid` defines open
question, stage gate, user-confirmation, and use-case symbols. `flows.mermaid`
defines the add-question, classify, confirm, and check-gate use cases.

## Boundaries

This epic does not own CLI output or document rendering. It owns the policy that
determines whether the current plan can move forward.

## Acceptance Criteria

- Every open question has an explanation.
- Blocking questions prevent advancement.
- Agents can add questions and mark them blocking.
- User confirmation is required for non-blocking classifications.
- Deferred questions carry a revisit stage.
