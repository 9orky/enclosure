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

## Step 02: Recipe Shell Calibration

### Route Receipt

- Files read:
  - `AGENTS.md`
  - `.enclosure/plans/CALIBRATION_REPORT.md`
  - `.enclosure/plans/PLAN_STEP_02.md`
  - `.enclosure/enclosure.yaml`
  - `.enclosure/rules/INDEX.md`
  - `.enclosure/rules/shared/INDEX.md`
  - `.enclosure/rules/shared/execution/INDEX.md`
  - `.enclosure/rules/shared/execution/STEP.md`
  - `.enclosure/rules/local/execution/INDEX.md`
  - `.enclosure/rules/local/execution/STEP.md`
  - `.enclosure/rules/shared/structure/INDEX.md`
  - `.enclosure/rules/shared/structure/FEATURE_LAYERS.md`
  - `.enclosure/rules/local/structure/INDEX.md`
  - `.enclosure/rules/local/structure/FEATURE_LAYERS.md`
  - `.enclosure/rules/local/structure/MODULE_LADDER.md`
  - `.enclosure/rules/shared/architecture/INDEX.md`
  - `.enclosure/rules/shared/architecture/DEPENDENCIES.md`
  - `.enclosure/rules/shared/verification/INDEX.md`
  - `.enclosure/rules/shared/verification/TESTING.md`
  - `src/enclosure/features/workspace/recipe/domain.py`
  - `src/enclosure/features/workspace/recipe/application.py`
  - `src/enclosure/features/workspace/recipe/ui/cli.py`
  - `src/enclosure/features/workspace/recipe/ui/templates/dry_run_result.tmpl`
  - `src/enclosure/features/workspace/recipe/ui/templates/recipe_summary.tmpl`
  - `tests/features/workspace/recipe/test_application.py`
  - `tests/features/workspace/recipe/test_functional.py`
- Reason: step 02 is an approved implementation-level artifact for the `workspace/recipe` module and its CLI preview seam.
- Stop point: existing recipe application, UI templates, and functional tests; owner, dependency direction, recipe shape, and verification seam were clear.
- Owner: `workspace/recipe` command and `.enclosure/recipes`.
- Public seam: `enclosure workspace recipe`, especially `--list`, `--show`, `--shell`, `--check`, and `--drifts`.
- Direction: CLI/UI consumes application reports; application consumes domain preview models and rendered recipe files; recipes remain contract input.
- Shape: `domain.py`, `application.py`, `infrastructure.py`, and `ui/` package remain the local module shape; no recipe or config contract was changed.
- Verification: focused recipe tests, `enclosure workspace recipe --check`, `enclosure workspace recipe --drifts`, and post-change `enclosure health`.

### Command Path Confirmed

- `enclosure workspace recipe --list` lists six available recipes.
- `enclosure workspace recipe module-workspace-cli --show` prints `enclosure workspace recipe module-workspace-cli <path> --shell`.
- `enclosure workspace recipe module-workspace-cli src/enclosure/features/workspace/recipe --shell` prints create/skip statuses, target paths, source templates, and rendered skeleton content without writing files.

### Baseline Recipe Drift

`enclosure workspace recipe --drifts` reports mechanical drift for three existing modules:

- `workspace/plan` with missing `application/__init__.py`, `application/commands.py`, and `application/queries.py`; extra `application.py`.
- `workspace/recipe` with missing `application/__init__.py`, `application/commands.py`, and `application/queries.py`; extra `application.py`.
- `workspace/sync` with missing `application/__init__.py`, `application/commands.py`, and `application/queries.py`; extra `application.py`.

This drift is a baseline legacy shape signal and was not fixed or suppressed in step 02.

### Focused Checks

- `uv run pytest tests/features/workspace/recipe/test_application.py tests/features/workspace/recipe/test_functional.py`
- `enclosure workspace recipe --check`
- `enclosure workspace recipe --drifts`
- `enclosure health`

### Step 02 Completion

Step 02 confirms that `--show` points to `--shell`, `--shell` proves the rendered module shell without writes, and baseline drift is named separately from preview behavior.
