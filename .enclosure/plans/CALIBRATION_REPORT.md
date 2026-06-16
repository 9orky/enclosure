# Calibration Report

## Step 01: Route And Contract Calibration

### Route Receipt

- Files read:
  - `AGENTS.md`
  - `.enclosure/rules/INDEX.md`
  - `.enclosure/rules/shared/INDEX.md`
  - `.enclosure/rules/shared/execution/INDEX.md`
  - `.enclosure/rules/shared/execution/CALIBRATION.md`
  - `.enclosure/rules/shared/execution/BIG_PICTURE.md`
  - `.enclosure/rules/shared/execution/STEP.md`
  - `.enclosure/rules/local/INDEX.md`
  - `.enclosure/rules/local/execution/INDEX.md`
  - `.enclosure/rules/local/execution/BIG_PICTURE.md`
  - `.enclosure/rules/local/execution/STEP.md`
  - `.enclosure/enclosure.yaml`
  - `.enclosure/plans/PLAN.md`
  - `.enclosure/plans/PLAN_STEP_01.md`
- Reason: step 01 is an approved execution artifact whose scope is discovery and contract interpretation before later implementation steps.
- Stop point: local execution step guidance. Structure and architecture rule branches are not needed for step 01 because the step does not edit feature code, reshape modules, or change boundaries.
- Owner: `.enclosure/rules` and `.enclosure/enclosure.yaml`.
- Public seam: generated workspace contract surfaces under `.enclosure/`, plus CLI verification commands.
- Direction: guidance and config constrain implementation; implementation does not redefine the contract during this step.
- Shape: compact feature modules under `src/enclosure/features` use `domain.py`, `infrastructure.py`, `application.py`, and `ui.py` when those responsibilities are needed.
- Verification: run `enclosure workspace rules`; after any change, run `enclosure health`.

### Focused Checks

- `enclosure workspace rules`
- `enclosure health`

### First-Read Guidance Gaps

- `.enclosure/AGENTS.md` is named by `.enclosure/plans/PLAN_STEP_01.md` but is absent from the workspace. The active first-read instruction is available from root `AGENTS.md`, and packaged guidance exists at `src/enclosure/resources/AGENTS.md`.

### Drift Stop Conditions

- Stop before implementation or contract edits if ownership, public seam, dependency direction, recipe shape, boundary flow, or health-check authority becomes unclear.
- Do not change `enclosure.yaml`, recipes, rule thresholds, exclusions, tags, or boundary rules merely to manufacture passing checks.

### Step 01 Completion

Step 01 records the route receipt pattern and the only first-read gap found. Later steps should consume this receipt before making implementation or contract changes.
