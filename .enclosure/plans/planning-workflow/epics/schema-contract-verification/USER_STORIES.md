# User Stories

## Navigation

- Epic: [Schema Contract Verification](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#schema-contract-verification) -> [PLAN.md](../../PLAN.md#schema-contract-verification) -> [UML.md](../../UML.md#slug-identity-contract)
- Siblings: [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## declare-stage-schema-contract

As the planner, I want every planning stage to implement a schema contract
interface so that schema ownership is part of the stage API.

Acceptance criteria:

- `StageSchemaContract` is defined beside `PlanningStage`.
- Concrete stages implement `StageSchemaContract`.
- Schema source declarations are returned by the owning stage.

## declare-native-schema-sources

As the epic stage, I want to declare native Mermaid files as schema sources so
that `flows.mermaid`, `uml.mermaid`, and `tree.mermaid` remain the SSOT.

Acceptance criteria:

- `EpicsStage` declares `flows.mermaid`.
- `EpicsStage` declares `uml.mermaid`.
- `EpicsStage` declares `tree.mermaid`.
- Draft and plan stages explicitly declare no native schema files.

## render-schema-display

As the epic stage, I want to render `SCHEMAS.md` from native Mermaid sources so
that the markdown page is a display projection.

Acceptance criteria:

- `SCHEMAS.md` is generated from `NativeSchemas`.
- Edits to generated `SCHEMAS.md` sections are not schema source edits.
- Later modwire comparison consumes the stage-owned native Mermaid files.
