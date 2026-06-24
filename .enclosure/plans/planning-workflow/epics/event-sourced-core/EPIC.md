# Event-Sourced Planning Core

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

- SQLite-backed event persistence is the local authority.
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

`tree.mermaid` defines the event core files. `uml.mermaid` defines the aggregate,
application, event, and use-case symbols. `flows.mermaid` defines the
event-sourced application use cases.

## Boundaries

This epic does not own markdown rendering, CLI interaction details, or epic
projection formats. It owns the source of truth that those layers depend on.
Its feature-specific ports follow the shared hexagonal shape, but the concrete
planning port methods remain owned here.

## Acceptance Criteria

- Plan creation appends durable events.
- Only one active plan can exist.
- Current plan state can be reconstructed from events.
- Event append behavior is atomic through SQLite persistence.
- Downstream projectors can consume ordered plan events.
