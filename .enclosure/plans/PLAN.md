# Enclosure Product Improvement Plan

## File Tree

```text
.enclosure/
  enclosure.yaml
  plans/
    PLAN.md
    PLAN_STEP_01.md
    PLAN_STEP_02.md
    PLAN_STEP_03.md
  rules/
    local/
    shared/
src/enclosure/
  features/
    health/
    workspace/
  resources/
  templates/
tests/
docs/
```

## Goal

Make `enclosure` a clearer product by turning the current contract-check loop into a guided, actionable, and workflow-integrated experience.

The plan covers three product improvements:

- sharper first-run onboarding;
- more actionable health output;
- better workflow integration.

## Strategic Model

`enclosure` should feel less like a toolbox of architecture commands and more like a repeatable operating loop for agentic coding:

1. start from the project contract;
2. discover the correct route;
3. make or review a change;
4. get concrete architectural feedback;
5. carry the result into CI, review, and assistant instructions.

The product should keep the repo-local contract as the source of truth. Improvements should explain and expose that contract, not replace it with a hosted workflow or hidden policy engine.

## Execution Frame

- Owner: product-facing CLI, generated guidance, health reports, and docs.
- Public seam: `enclosure --llm`, `enclosure workspace sync`, `enclosure workspace rules`, `enclosure workspace recipe`, `enclosure health`, and CI-friendly command output.
- Direction: workspace contract and rules remain source input; commands and guidance render that contract into user-facing workflows.
- Shape: prefer changes inside existing compact feature modules under `src/enclosure/features`; add new modules only if existing ownership cannot carry the work.
- Verification: highest practical seam is CLI output plus focused tests for command docs, health reports, and workspace sync behavior.

## Phases

### Phase 1: First-Run Onboarding

- Objective: make a new user or agent understand the first useful path within one short command sequence.
- Owner: workspace sync, root guidance templates, README quick start, and command docs.
- Inputs: current README quick start, `enclosure --llm`, generated `AGENTS.md`, workspace sync init/update behavior, recipe preview guidance, and existing command docs tests.
- Outputs: a guided first-run path that shows how to initialize, inspect, draft or refine the contract, preview recipes, run health, and choose the next action.
- Acceptance: docs and generated guidance name one primary onboarding path; command examples validate; a user can distinguish initialization, inspection, recipe preview, and health checks without inferring flag combinations.

### Phase 2: Actionable Health Output

- Objective: turn health findings into prioritized next actions instead of raw attention signals.
- Owner: health report surfaces and the architecture/workspace reports they aggregate.
- Inputs: `enclosure health`, `enclosure architecture health`, recipe drift output, boundary and shape reports, pressure/coherence/clusters findings, and current health tests.
- Outputs: health summaries that separate blockers, baseline drift, attention findings, and suggested remediation commands.
- Acceptance: health output identifies whether a finding should block review, be migrated later, or be investigated; known drift can be named without suppressing violations; tests cover at least one blocker, one drift item, and one attention-level finding.

### Phase 3: Workflow Integration

- Objective: make enclosure feedback usable in CI, PR review, editor surfaces, and agent handoffs.
- Owner: CLI output formats, sync-carried instructions, and documentation for automation.
- Inputs: current CLI command surfaces, command docs, generated assistant instructions, health/rules/recipe checks, and repository CI expectations.
- Outputs: machine-readable or review-friendly output for core checks, documented CI command examples, and synced instructions that tell agents exactly what to run before and after changes.
- Acceptance: CI examples run through docs validation; command output has a stable automation path; generated agent instructions include pre-change route discovery and post-change health verification.

## Acceptance

- `.enclosure/plans/PLAN.md` remains phase-level.
- Approved phases have matching `PLAN_STEP_0X.md` files.
- Each phase names objective, owner, inputs, outputs, and acceptance.
- The plan keeps implementation detail out of the big picture.
- Focused checks after this planning change:
  - `enclosure workspace rules`
  - `enclosure health`

## Open Questions

- Should onboarding become a new command, a documented command sequence, or enhanced `--llm` guidance first?
- Should actionable health suggestions be plain text only, or should they share a structured model with future JSON output?
- Which workflow integration should ship first: CI examples, JSON output, PR annotations, or editor-friendly summaries?
