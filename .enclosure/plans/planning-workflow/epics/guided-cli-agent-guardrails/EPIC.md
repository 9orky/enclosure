---
plan_id: planning-workflow
epic_id: guided-cli-agent-guardrails
title: Guided CLI and Agent Guardrails
ordinal: 4
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
  - projected-documents
  - stage-gates-open-questions
blocks: []
owns:
  - workspace plan status
  - workspace plan start
  - workspace plan next
  - workspace plan agent
  - allowed command guidance
---

# Guided CLI and Agent Guardrails

## Value

This epic makes the planning workflow usable from VS Code with Codex while
limiting unexpected agent behavior. The CLI tells users and agents what state
the plan is in and which commands are currently valid.

## Outcome

The command loop is simple: start a plan, edit projected input blocks, import and
check with `next`, ask the agent for constrained guidance, and advance only when
the gate allows it.

## Navigation

Previous dependencies:

- Event-Sourced Planning Core
- Projected Planning Documents
- Stage Gates and Open Questions

Next dependent epic: none.

## Contract Role

`tree.mermaid` defines CLI and guidance files. `uml.mermaid` defines CLI,
next-action, agent-guidance, and use-case symbols. `flows.mermaid` defines the
status, next, agent-guidance, and allowed-action use cases.

## Boundaries

This epic does not own the domain rules themselves. It owns how users and agents
invoke those rules safely.

## Acceptance Criteria

- `workspace plan status` reports active plan, stage, sync, and blockers.
- `workspace plan start <name>` creates the active plan and first projection.
- `workspace plan next` imports marked blocks, checks gates, and reports allowed
  moves.
- `workspace plan agent` produces constrained agent guidance.
- The agent guidance never grants permission to run arbitrary plan mutations.
