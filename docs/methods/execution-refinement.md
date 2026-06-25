# Execution Refinement Method

Execution refinement is the stage-loop method for narrowing uncertainty without
losing the approved contract.

The refinement chain is:

```text
calibration -> draft -> plan -> epics -> implementation -> reconciliation
```

## Calibration

Calibration discovers the active contract:

- project root and architecture root,
- relevant shared branch,
- local rule supplements,
- current owner and seam,
- dependency direction,
- recipe role when a target is recipe-shaped.

Do not configure stages from memory when the contract can be read.

## Stage Loop

Planning is the agent's process of self-configuring workspace plan stages until
epics are materialized. The user may also run this process, but the agent is
preferred because it can keep discovery, stage artifacts, questions, and
verification aligned.

Draft is only the first stage. An agent must continue the loop after draft
unless the active plan is blocked, explicitly paused, or closed by the user.

Use `workspace plan agent`, `workspace plan put`, `workspace plan ask`,
`workspace plan answer`, and `workspace plan next` to keep stage artifacts inside
the event-sourced workspace plan.

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
