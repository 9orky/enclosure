# Step 04: Health And Drift Reconciliation

## Implementation Tree

```text
.enclosure/
  enclosure.yaml
  plans/
    PLAN.md
    PLAN_STEP_04.md
src/enclosure/features/
  workspace/health/
    application.py
    domain.py
    ui/cli.py
  workspace/recipe/
    application.py
      check_recipe_drifts(...)
  architecture/health/
  architecture/boundaries/
  architecture/shape/
```

## Goal

Separate actionable regressions from known baseline attention findings after self-calibration work.

## Step Contract

- Inputs: `enclosure workspace rules`, `enclosure workspace recipe --check`, `enclosure workspace recipe --drifts`, `enclosure health`.
- Outputs: reconciliation report naming pass/fail checks, known recipe drift, architecture attention findings, and contract-change stop conditions.
- Scope: verification and reporting only.
- Out of scope: fixing drift, changing thresholds, changing exclusions, or suppressing findings.
- Owner: workspace health and architecture health reports.
- Dependency direction: health consumes config, rules, recipes, and architecture scans; health findings do not rewrite the contract.

## Execution

1. Run `enclosure workspace rules` and record rule schema status.
2. Run `enclosure workspace recipe --check` and record recipe validation status.
3. Run `enclosure workspace recipe --drifts` and classify missing/extra recipe files as baseline or regression.
4. Run `enclosure health` and record workspace, boundaries, shape, pressure, clusters, and coherence findings.
5. Stop if boundaries or shape regress, or if recipe drift appears outside known baseline modules.

## Verification

- Rules report 0 documents with issues.
- Recipes report 0 violations.
- `enclosure health` reports 0 boundary violations and 0 shape violations.
- Known attention findings are named without changing config.

## Completion

Incomplete until the calibration report distinguishes clean checks, baseline drift, and attention-level architecture findings without weakening the contract.
