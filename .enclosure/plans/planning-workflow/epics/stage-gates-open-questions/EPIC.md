# Stage Gates and Open Questions

## Navigation

- Draft source: [Stage Gates and Open Questions](../../DRAFT.md#stage-gates-and-open-questions)
- Plan source: [stage-gates-open-questions](../../PLAN.md#stage-gates-open-questions)
- Technical id contract: [UML.md](../../UML.md#slug-identity-contract)
- Epic artifacts: [USER_STORIES.md](USER_STORIES.md), [SCHEMAS.md](SCHEMAS.md), [flows.mermaid](flows.mermaid), [uml.mermaid](uml.mermaid), [tree.mermaid](tree.mermaid)

## Source Chain

```text
draft_use_case_id: stage-gates-open-questions
plan_item_id: stage-gates-open-questions
epic_id: stage-gates-open-questions
```

This epic reuses the draft use case and plan item for
`stage-gates-open-questions`. The slug stays stable because no split rule
creates variants for this example.

## Reused Plan Data

Intent: make uncertainty explicit so stages cannot advance while blocking
questions remain unresolved or while agent-suggested unblocking lacks user
confirmation.

Planned outcome: every stage can add, classify, confirm, and evaluate Open
Questions before accepting stage output.

Accepted constraints:

- Every question needs an explanation.
- Blocking questions stop advancement.
- Agent-suggested non-blocking classifications require user confirmation.
- Deferred questions need a revisit stage.

## Value

This epic prevents plans from advancing while important uncertainty is silently
ignored. It makes open questions first-class, explained, classified, and enforced
by stage gates.

## Outcome

Every stage uses the same scaffold, agent update, user review, gate, and `next`
acceptance loop. Questions can block progress, and agents cannot silently
unblock their own uncertainty.

## Navigation

Previous dependencies:

- Hexagonal Foundation
- Event-Sourced Planning Core

Next dependent epic:

- Guided CLI and Agent Guardrails

## Contract Role

`tree.mermaid` defines gate and question files. `uml.mermaid` defines open
question, stage gate, user-confirmation, and use-case symbols. `flows.mermaid`
defines the question, classification, confirmation, and gate-check signals used
inside the stage loop.

## Boundaries

This epic does not own CLI output or document rendering. It owns the policy that
determines whether the current plan can move forward.

## Acceptance Criteria

- Every open question has an explanation.
- Blocking questions prevent advancement.
- Agents can add questions and mark them blocking.
- User confirmation is required for non-blocking classifications.
- Deferred questions carry a revisit stage.
