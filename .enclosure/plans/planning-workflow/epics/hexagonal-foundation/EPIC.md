# Hexagonal Foundation

## Navigation

- Draft source: [Hexagonal Foundation](../../DRAFT.md#hexagonal-foundation)
- Plan source: [hexagonal-foundation](../../PLAN.md#hexagonal-foundation)
- Technical id contract: [UML.md](../../UML.md#slug-identity-contract)
- Epic artifacts: [USER_STORIES.md](USER_STORIES.md), [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## Source Chain

```text
draft_use_case_id: hexagonal-foundation
plan_item_id: hexagonal-foundation
epic_id: hexagonal-foundation
```

This epic reuses the draft use case and plan item for `hexagonal-foundation`.
The slug stays stable because no split rule creates variants for this example.

## Reused Plan Data

Intent: define shared port, adapter, and dependency-shape vocabulary before the
planning module starts adding concrete event stores, projection stores, schema
providers, or CLI adapters.

Planned outcome: `shared.hexagonal` exposes protocol-style contracts and adapter
metadata that the planning module can use without collapsing concrete planning
behavior into shared code.

Accepted constraints:

- Shared contracts do not contain planning-specific behavior.
- Domain code remains independent of application, infrastructure, and UI.
- Concrete planning ports remain owned by the planning module.

## Value

This epic gives the planning module a shared interface vocabulary before the
event-sourced implementation starts. Ports, adapters, and application-facing
interfaces should have a consistent shape without forcing every concrete
implementation into a shared inheritance hierarchy.

## Outcome

`shared.hexagonal` defines the small set of protocol-style contracts and adapter
metadata needed to keep feature modules aligned. Planning-specific ports remain
owned by the planning module, but they follow the shared shape.

## Navigation

Previous epic: none.

Next dependent epics:

- Event-Sourced Planning Core
- Projected Planning Documents
- Stage Gates and Open Questions
- Guided CLI and Agent Guardrails
- Schema Contract Verification

## Contract Role

`tree.mermaid` defines the shared hexagonal files. `uml.mermaid` defines the
protocol, port, adapter, and dependency-shape symbols. `flows.mermaid` defines
how later feature-specific ports and adapters use the shared contracts.

## Boundaries

This epic does not own concrete planning ports such as `EventStore`,
`ProjectionStore`, or `ModwireSchemaProvider`. It owns only the shared
interface shape, adapter metadata, and checks that keep dependencies flowing
through ports instead of deep imports.

## Acceptance Criteria

- `shared.hexagonal` exposes protocol-style interfaces for ports and adapters.
- Concrete feature ports can opt into the shared port shape without inheriting
  behavior they do not need.
- Adapter declarations identify the port they implement.
- Application code depends on ports, not adapter internals.
- Domain code remains independent of application, infrastructure, and UI
  contracts.
- The shared package does not define planning-specific ports.
