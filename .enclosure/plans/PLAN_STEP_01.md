# Step 01: Route And Contract Calibration

## Implementation Tree

```text
.enclosure/
  AGENTS.md
  enclosure.yaml
  plans/
    PLAN.md
    PLAN_STEP_01.md
  rules/
    INDEX.md
    shared/execution/CALIBRATION.md
    shared/execution/BIG_PICTURE.md
    shared/execution/STEP.md
    local/INDEX.md
    local/execution/BIG_PICTURE.md
    local/execution/STEP.md
src/enclosure/
  templates/llm.tmpl
  resources/AGENTS.md
```

## Goal

Confirm the minimal rule route an agent should read before editing this repository and record the route receipt pattern expected by the contract.

## Step Contract

- Inputs: `.enclosure/AGENTS.md`, `.enclosure/enclosure.yaml`, shared/local execution rules, and any task-specific structure or architecture rules reached by routing.
- Outputs: confirmed route receipt for self-calibration and a list of first-read guidance gaps, if any.
- Scope: discovery and contract interpretation only.
- Out of scope: editing implementation code, changing rules, changing recipes, or weakening checks.
- Owner: `.enclosure/rules` and `.enclosure/enclosure.yaml`.
- Dependency direction: guidance and config constrain implementation; implementation does not redefine the contract during this step.

## Execution

1. Start in `.enclosure/` and read `rules/INDEX.md`.
2. Route through shared execution guidance to calibration and step rules.
3. Read local execution supplements after the shared branch is in scope.
4. Inspect `enclosure.yaml` for architecture root, tags, layer direction, recipes, and verification commands.
5. Emit the route receipt before any later implementation step: files read, reason, stop point, focused checks, and post-change `enclosure health`.
6. Stop if ownership, dependency direction, or contract authority is unclear.

## Verification

- Run `enclosure workspace rules`.
- Confirm rule schema reports 0 documents with issues.
- Confirm the route receipt names owner, seam, direction, shape, and verification.

## Completion

Incomplete until the route receipt is recorded in the calibration report and any first-read gaps are either named for later phases or explicitly marked as absent.
