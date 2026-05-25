---
doc_class: execution
rule_kind: execution
audience: agent
purpose: Define one approved phase as an implementation-level execution artifact.
applies_when:
  - A big-picture phase has been approved.
  - The next execution artifact needs implementation detail.
tags:
  - execution
  - step
stage: step
same_artifact_family: execution
read_directly: false
escalation_paths: []
---

# Step

## Required Sections

- `Implementation Tree`
- `Goal`
- `Step Contract`
- `Execution`
- `Verification`
- `Completion`

## Implementation Tree Rules

- Put `Implementation Tree` first.
- Name the artifact `PLAN_STEP_0X.md`.
- Match `0X` to approved phase order.
- Reuse the big-picture tree and add planned signatures.

## Step Contract Rules

- State inputs, outputs, scope, out-of-scope, owner, and dependency direction.
- Keep the step narrow enough to finish and verify.

## Execution Rules

- Use ordered work items.
- Adapt locally only when goal and boundary stay intact.
- Stop when ownership, boundary, or dependency assumptions break.

## Review Checks

- Tree first, step filename correct, signatures present.
- Scope and verification are narrow.
- Completion state is explicit.

## Handoff Checks

- Step still matches the approved phase.
- Drift is recorded before proceeding.
