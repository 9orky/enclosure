---
doc_class: execution
rule_kind: execution
audience: agent
purpose: Define the human-approved calibration protocol before architecture-sensitive agent work.
applies_when:
  - The agent must learn or adapt a project contract before implementation.
  - The work may change local rules, recipes, module ownership, public seams, or dependency direction.
tags:
  - execution
  - calibration
  - drift
stage: calibration
same_artifact_family: execution
read_directly: false
escalation_paths:
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
  - ../architecture/DEPENDENCIES.md
  - ../structure/MODULE_LADDER.md
---

# Calibration

## Protocol Position

- Run calibration before `PLAN.md` when the project contract is not already clear.
- Use calibration to discover and confirm rules, not to implement code.
- Continue to big-picture planning only after human approval of unresolved contract choices.

## Required Activities

- Route: read the shallowest matching shared rule branch, then local supplements.
- Calibrate: identify architecture root, ownership, module shape, slots, seams, dependency direction, recipe ladder, and verification seam.
- Frame: turn approved calibration decisions into the phase-level `PLAN.md`.
- Contract: turn approved phases into narrow `PLAN_STEP_0X.md` step contracts.
- Execute: adapt locally only while approved owner, seam, direction, and goal stay intact.
- Reconcile: compare the result with the route, ladder, boundaries, shape, health, and tests.
- Codify: propose durable project discoveries as narrow local rule supplements.

## Human Gates

- Calibration gate: approve discovered project contract before changing local guidance.
- Plan gate: approve `PLAN.md` phases before step artifacts exist.
- Step gate: approve each `PLAN_STEP_0X.md` before implementation.
- Drift gate: stop when ownership, seam, dependency direction, or recipe shape assumptions break.
- Codification gate: approve turning one-time discovery into local rules.

## Drift Controls

- Emit a route receipt before edits: files read, reason, stop point, focused checks to run, and post-change `enclosure health`.
- Treat local rules as narrowing shared rules, not restating shared policy.
- Keep recipe drift mechanical: missing required seams, forbidden file/package combinations, and extra root files outside declared slots.
- Depend on public seams instead of private internals.
- Stop on cycles, backward flow, unclear ownership, or API widening done only for convenience.
- Verify through the highest valid public seam when practical.

## Codification Rules

- Put durable structure facts under local structure rules.
- Put local phase or step order under local execution rules.
- Put refactoring policy under local change rules.
- Keep recipes focused on file and package shape contracts.
- Do not codify a one-off implementation detail as a project rule.

## Review Checks

- Calibration decisions name owner, seam, direction, shape, and verification.
- Human gates are explicit before implementation begins.
- Drift stop conditions are recorded before work proceeds.

## Handoff Checks

- `PLAN.md` receives only approved calibration decisions.
- Local rule proposals narrow a shared rule and name their shared anchor.
- Checks include post-change `enclosure health`, workspace rules when rule or workspace contract files change, and the architecture checks affected by the decision.
