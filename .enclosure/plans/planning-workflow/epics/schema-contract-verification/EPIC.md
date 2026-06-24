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

Planned outcome: the planner can parse planned contracts, derive actual schemas,
compare them, and report missing, extra, or mismatched implementation targets.

Accepted constraints:

- `tree.mermaid` defines expected files.
- `uml.mermaid` defines expected symbols and file annotations.
- `flows.mermaid` defines parseable command, use-case, domain, and output flow.
- Actual schemas come from filesystem and modwire-derived structure.

## Value

This epic turns Mermaid schemas into enforceable implementation contracts. The
planner can compare planned file, symbol, and flow contracts with actual
implementation structure after an agent writes code.

## Outcome

Enclosure can report whether implementation matches the planned `tree.mermaid`,
`uml.mermaid`, and `flows.mermaid` contracts and can give the agent focused
repair instructions when drift appears.

## Boundaries

This epic does not own the plan event store or markdown projection renderer. It
owns schema extraction, contract comparison, and drift reporting.

## Navigation

Previous dependencies:

- Hexagonal Foundation
- Event-Sourced Planning Core
- Projected Planning Documents

Next dependent epic: none.

## Contract Role

`tree.mermaid` defines which verification files and modules this epic expects.
`uml.mermaid` defines the contract classes and methods that perform comparison.
`flows.mermaid` defines the parse, derive-actual, compare, and report use cases.

## Acceptance Criteria

- Planned `tree.mermaid` can be parsed into expected files.
- Planned `uml.mermaid` can be parsed into expected symbols.
- Actual implementation structure can be obtained from modwire.
- Planned and actual schemas can be compared.
- Drift reports identify missing, extra, and mismatched files or symbols.
- Agent-facing repair instructions reference the exact contract mismatch.
