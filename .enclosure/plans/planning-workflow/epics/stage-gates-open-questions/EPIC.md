# Stage Gates and Open Questions

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
