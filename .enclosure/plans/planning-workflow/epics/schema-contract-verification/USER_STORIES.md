# User Stories

## Navigation

- Epic: [Schema Contract Verification](EPIC.md)
- Source chain: [DRAFT.md](../../DRAFT.md#schema-contract-verification) -> [PLAN.md](../../PLAN.md#schema-contract-verification) -> [UML.md](../../UML.md#slug-identity-contract)
- Siblings: [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## parse-planned-contracts

As the planner, I want to parse planned Mermaid files so that diagrams become
machine-checkable contracts.

Acceptance criteria:

- `tree.mermaid` produces an expected file list.
- `uml.mermaid` produces expected classes, methods, properties, and relations.
- `flows.mermaid` produces expected use-case nodes with file and class targets.

## derive-actual-schemas

As the verifier, I want to query actual implementation structure through modwire
so that the codebase can be compared with the plan.

Acceptance criteria:

- Actual files can be listed for the planned scope.
- Actual symbols can be mapped back to source files.
- Actual schema output can be normalized into the same comparison model as the
  planned contracts.

## report-contract-drift

As an agent, I want precise drift reports so that I can repair code according to
the plan instead of guessing.

Acceptance criteria:

- Missing planned files are reported.
- Unexpected files are reported.
- Missing or mismatched classes, properties, and methods are reported.
- Reports include suggested repair targets.
