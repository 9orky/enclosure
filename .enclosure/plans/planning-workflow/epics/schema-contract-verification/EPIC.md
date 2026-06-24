# Schema Contract Verification

## Navigation

- Draft source: [Schema Contract Verification](../../DRAFT.md#schema-contract-verification)
- Plan source: [schema-contract-verification](../../PLAN.md#schema-contract-verification)
- Technical id contract: [UML.md](../../UML.md#slug-identity-contract)
- Epic artifacts: [USER_STORIES.md](USER_STORIES.md), [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## Source Chain

```text
draft_use_case_id: schema-contract-verification
plan_item_id: schema-contract-verification
epic_id: schema-contract-verification
```

This epic reuses the draft use case and plan item for
`schema-contract-verification`. The slug stays stable because no split rule
creates variants for this example.

## Reused Plan Data

Intent: compare accepted Mermaid file, symbol, and flow contracts with actual
implementation structure so agents can repair drift precisely.

Planned outcome: stages declare their native Mermaid schema sources through a
stage-owned interface, render `SCHEMAS.md` from those native sources, and leave
modwire comparison to consume those stage-owned sources later.

Accepted constraints:

- `tree.mermaid` defines the stage-owned schema interface files.
- `uml.mermaid` defines `StageSchemaContract`, native schema source metadata,
  and the concrete stage implementations that own schema declarations.
- `flows.mermaid` defines the stage-owned schema source and display projection
  flow.
- Actual modwire comparison consumes stage-owned native Mermaid files later.

## Value

This epic anchors Mermaid schemas in the stage contract. The planner can tell
which native Mermaid files a stage owns and can render the display-only
`SCHEMAS.md` from those native sources without inventing schema ownership
outside the stage.

## Outcome

Stages expose their schema source files as part of their interface. `EpicsStage`
owns `flows.mermaid`, `uml.mermaid`, `tree.mermaid`, and the `SCHEMAS.md`
display projection.

## Boundaries

This epic does not own the plan event store. It owns the stage-side schema
declaration interface and the display projection method that pastes native
Mermaid into `SCHEMAS.md`.

## Navigation

Previous dependencies:

- Hexagonal Foundation
- Event-Sourced Planning Core
- Projected Planning Documents

Next dependent epic: none.

## Contract Role

`tree.mermaid` defines the stage-owned schema contract files. `uml.mermaid`
defines the `StageSchemaContract` interface and concrete stage implementations.
`flows.mermaid` defines how stages declare native Mermaid schema files and
render `SCHEMAS.md` as a display projection.

## Acceptance Criteria

- Stages implement `StageSchemaContract`.
- `EpicsStage` declares `flows.mermaid`, `uml.mermaid`, and `tree.mermaid` as
  native schema sources.
- `SCHEMAS.md` is rendered from native Mermaid source by the owning stage.
- Later modwire comparison consumes stage-owned native Mermaid files.
