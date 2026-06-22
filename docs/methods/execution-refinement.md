# Execution Refinement Method

Execution refinement is the method for narrowing uncertainty without losing the
approved contract.

The refinement chain is:

```text
calibration -> PLAN.md -> PLAN_STEP_0X.md -> implementation -> reconciliation
```

## Calibration

Calibration discovers the active contract:

- project root and architecture root,
- relevant shared branch,
- local rule supplements,
- current owner and seam,
- dependency direction,
- recipe role when a target is recipe-shaped.

Do not plan from memory when the contract can be read.

## Phase Plan

`PLAN.md` is phase-level. It names file tree, goal, phases, acceptance, and open
questions. It should not contain function-level implementation detail.

Approved phase order becomes step order.

## Step Plan

`PLAN_STEP_0X.md` refines one approved phase. It names implementation tree, step
contract, ordered execution items, verification, and completion state.

Implementation is valid only while these remain unchanged:

- goal,
- owner,
- public seam,
- dependency direction,
- scope.

## Reconciliation

At the end of a meaningful change:

- verify the route still matches the touched files,
- check that seams stayed narrow,
- check that recipe roles still describe module shape,
- run focused architecture and behavior checks,
- document method changes only when the method itself changed.

This is a proof discipline: each stage narrows uncertainty and preserves stated
assumptions.
