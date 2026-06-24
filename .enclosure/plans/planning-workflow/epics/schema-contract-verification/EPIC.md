# Schema Contract Verification

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
