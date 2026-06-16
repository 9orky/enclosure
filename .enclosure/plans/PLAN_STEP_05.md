# Step 05: Codification Decision

## Implementation Tree

```text
.enclosure/
  plans/
    PLAN.md
    PLAN_STEP_05.md
  rules/
    local/
      execution/
      structure/
      change/
    shared/
src/enclosure/
  resources/rules/
  features/workspace/recipe/
docs/
  modules/
```

## Goal

Decide which self-calibration discoveries should become durable local rules, packaged guidance, recipe/docs changes, or no change.

## Step Contract

- Inputs: outputs from steps 01-04, known drift report, command docs validation, and health findings.
- Outputs: explicit keep/change/defer decisions for each discovery.
- Scope: codification decision and narrow follow-up proposal.
- Out of scope: implementing codification not approved by the human gate.
- Owner: local rule supplements and packaged guidance only when justified.
- Dependency direction: durable observations narrow existing shared anchors; local rules do not restate shared policy.

## Execution

1. Review route, recipe shell, sync guidance, and health reconciliation outcomes.
2. Classify each discovery as `codify`, `keep local`, `defer`, or `discard`.
3. For `codify`, name the exact shared anchor and local/package target.
4. For `defer`, name the trigger that would reopen the decision.
5. Stop before editing `enclosure.yaml`, recipes, or rule files unless the contract-change or codification gate is explicitly approved.

## Verification

- Run `enclosure workspace rules` after any approved rule codification.
- Run `enclosure workspace recipe --check` after any approved recipe/docs codification.
- Run `enclosure health` after any approved contract change.

## Completion

Incomplete until the final calibration report states which discoveries were codified, which were deferred, and which remain one-time observations.
