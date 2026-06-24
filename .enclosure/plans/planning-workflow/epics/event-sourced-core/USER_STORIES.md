# User Stories

## Navigation

- Epic: [Event-Sourced Planning Core](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#event-sourced-planning-core) -> [PLAN.md](../../PLAN.md#event-sourced-core) -> [UML.md](../../UML.md#slug-identity-contract)
- Siblings: [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## create-active-plan

As a workspace user, I want to start one active plan so that all later planning
commands operate on a single unambiguous planning context.

Acceptance criteria:

- Starting a plan records a `Plan.Created` aggregate event.
- Starting a second active plan is rejected.
- `workspace plan` status can identify the active plan without scanning
  projected files.

## append-plan-events

As the planning module, I want every meaningful plan change to append a domain
event so that planning history is durable and inspectable.

Acceptance criteria:

- Draft updates, question changes, accepted stage outputs, stage advances,
  projection records, and roll requests append nested `Plan` aggregate events.
- Events are recorded through the `eventsourcing` application and persisted in
  SQLite.
- Failed commands do not leave partial state.

## reconstruct-plan-state

As an agent or command, I want the current plan state reconstructed from events
so that decisions are based on the authoritative model.

Acceptance criteria:

- Application queries rebuild current state from event history.
- Reconstructed state includes current stage, active flag, questions, and known
  projections.
- Projectors do not read projected markdown as the authority.
- Downstream consumers can read ordered events from the `eventsourcing`
  notification log.
