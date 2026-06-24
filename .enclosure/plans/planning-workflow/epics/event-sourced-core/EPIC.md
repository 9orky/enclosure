# Event-Sourced Planning Core

## Navigation

- Draft source: [Event-Sourced Planning Core](../../DRAFT.md#event-sourced-planning-core)
- Plan source: [event-sourced-core](../../PLAN.md#event-sourced-core)
- Technical id contract: [UML.md](../../UML.md#slug-identity-contract)
- Epic artifacts: [USER_STORIES.md](USER_STORIES.md), [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## Source Chain

```text
draft_use_case_id: event-sourced-core
plan_item_id: event-sourced-core
epic_id: event-sourced-core
```

This epic reuses the draft use case and plan item for `event-sourced-core`.
The slug stays stable because no split rule creates variants for this example.

## Reused Plan Data

Intent: create the authoritative planning model so plan creation, stage
transitions, question changes, projection registration, and roll requests are
stored as events and reconstructed into current state.

Planned outcome: the workspace can create one active plan, append durable
events, and reconstruct the current plan state through the planning application.

Accepted constraints:

- SQLite-backed event persistence is the local authority through the
  `eventsourcing` library's SQLite persistence module.
- Only one active plan may exist.
- Projectors consume events and do not treat markdown as the database.

## Value

This epic gives the planning module a reliable authority model. Instead of
treating markdown files as the database, plan facts are appended as durable
events and reconstructed into current state when commands run.

## Outcome

The workspace can create one active plan, record plan changes in SQLite, and
reconstruct the current plan state through the planning application.

## Navigation

Previous dependency:

- Hexagonal Foundation

Next dependent epics:

- Projected Planning Documents
- Guided CLI and Agent Guardrails
- Stage Gates and Open Questions
- Schema Contract Verification

## Contract Role

`tree.mermaid` defines the flattened event core files. `uml.mermaid` defines
the `eventsourcing` aggregate, application, nested event-class SSOT,
persistence, workspace facade, and minimal UI symbols that already exist.
`flows.mermaid` defines the implemented start/status/advance/roll paths.

## Boundaries

This epic does not own markdown projection formats, agent guidance, or schema
comparison. It owns the flattened source-of-truth module
that those later layers depend on, plus the minimal `workspace plan` and
`workspace plan start TITLE` shell implemented around that source of truth.
Event recording, reconstruction, optimistic concurrency, and ordered
notifications are delegated to the `eventsourcing` library rather than
reimplemented locally.

## Acceptance Criteria

- Plan creation appends durable events.
- Only one active plan can exist.
- Current plan state can be reconstructed from events.
- Event append behavior is atomic through SQLite persistence.
- Downstream projectors can consume ordered plan events.
