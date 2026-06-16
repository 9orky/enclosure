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

## Step 03: Guidance Sync Calibration

### Route Receipt

- Files read:
  - `AGENTS.md`
  - `.enclosure/plans/CALIBRATION_REPORT.md`
  - `.enclosure/plans/PLAN_STEP_03.md`
  - `.enclosure/rules/INDEX.md`
  - `.enclosure/rules/shared/INDEX.md`
  - `.enclosure/rules/shared/execution/INDEX.md`
  - `.enclosure/rules/shared/execution/STEP.md`
  - `.enclosure/rules/shared/structure/INDEX.md`
  - `.enclosure/rules/shared/structure/MODULE_LADDER.md`
  - `src/enclosure/resources/AGENTS.md`
  - `src/enclosure/resources/rules/shared/structure/MODULE_LADDER.md`
  - `src/enclosure/templates/llm.tmpl`
  - `src/enclosure/features/workspace/recipe/ui/templates/docs.tmpl`
  - `src/enclosure/features/workspace/recipe/ui/templates/llm.tmpl`
  - `tests/ui/test_command_docs.py`
- Reason: step 03 is an approved guidance-sync calibration for the surfaces agents read before recipe-shaped implementation.
- Stop point: root LLM guidance, packaged shared module-ladder rule, current workspace module-ladder rule, and command-docs validation surface; sync policy changes were not needed.
- Owner: packaged resources under `src/enclosure/resources` and guidance templates under `src/enclosure/templates`.
- Public seam: rendered `enclosure --llm`, synced `.enclosure/rules/shared/structure/MODULE_LADDER.md`, and validated command examples.
- Direction: packaged resources flow into `.enclosure/` through sync; local rules narrow shared guidance after update.
- Shape: guidance remains in packaged resources and templates; no local config, sync overwrite policy, or command surface was changed.
- Verification: `uv run pytest tests/ui/test_command_docs.py`, `enclosure workspace rules`, and post-change `enclosure health`.

### Guidance Path Confirmed

- `enclosure --llm` names `enclosure workspace recipe --list`, `--show`, and `enclosure workspace recipe <name> <path> --shell` in the agent operating loop.
- `src/enclosure/resources/rules/shared/structure/MODULE_LADDER.md` names `enclosure workspace recipe <name> <path> --shell` before recipe-shaped code is implemented.
- `.enclosure/rules/shared/structure/MODULE_LADDER.md` matches the packaged module-ladder guidance, so this self-calibrating workspace already has the synced rule text.
- `src/enclosure/features/workspace/recipe/ui/templates/docs.tmpl` and `llm.tmpl` both advertise `--shell` as the agent-facing shell preview path.

### Focused Checks

- `uv run pytest tests/ui/test_command_docs.py`
- `enclosure workspace rules`
- `enclosure health`

### Step 03 Completion

Step 03 confirms that root LLM guidance, packaged module-ladder guidance, the current workspace shared rule, and command-docs validation expose `--shell` as the simple agent path.

## Step 04: Health And Drift Reconciliation

### Route Receipt

- Files read:
  - `AGENTS.md`
  - `.enclosure/plans/CALIBRATION_REPORT.md`
  - `.enclosure/plans/PLAN_STEP_04.md`
  - `.enclosure/rules/INDEX.md`
  - `.enclosure/rules/shared/INDEX.md`
  - `.enclosure/rules/shared/execution/INDEX.md`
  - `.enclosure/rules/shared/execution/STEP.md`
  - `.enclosure/rules/shared/verification/INDEX.md`
  - `.enclosure/rules/shared/verification/TESTING.md`
- Reason: step 04 is an approved verification and reconciliation artifact.
- Stop point: public CLI verification seam; the step does not alter health, recipe, rules, or architecture implementation.
- Owner: workspace health and architecture health reports.
- Public seam: `enclosure workspace rules`, `enclosure workspace recipe --check`, `enclosure workspace recipe --drifts`, and `enclosure health`.
- Direction: health consumes config, rules, recipes, and architecture scans; health findings do not rewrite the contract.
- Shape: no implementation shape change; reconciliation is recorded in this report only.
- Verification: the four step 04 CLI checks listed below.

### Clean Checks

- `enclosure workspace rules`: 33 documents checked, 0 documents with issues, 13 local documents checked, complete collection coverage.
- `enclosure workspace recipe --check`: 6 recipes discovered, 6 recipes checked, 30 rendered paths checked, 0 violations.
- `enclosure health`: workspace config, rules, and recipes present and clean; architecture boundaries report 0 violations; shape reports 0 violations; map reports 4 modules, 0 cross-module dependency paths, and 0 unknown files.

### Baseline Recipe Drift

`enclosure workspace recipe --drifts` exits nonzero because three mapped modules still use the legacy compact `application.py` file while their mapped `module-workspace-cli` recipe now expects an `application/` package:

- `workspace/plan`: missing `application/__init__.py`, `application/commands.py`, and `application/queries.py`; extra `application.py`.
- `workspace/recipe`: missing `application/__init__.py`, `application/commands.py`, and `application/queries.py`; extra `application.py`.
- `workspace/sync`: missing `application/__init__.py`, `application/commands.py`, and `application/queries.py`; extra `application.py`.

This matches the step 02 baseline and is not a new regression.

### Attention Findings

`enclosure health` reports attention-level architecture findings:

- `architecture/pressure`: 1712 unresolved calls.
- `architecture/coherence`: 26 coherence findings across 15 streams.
- `architecture/clusters`: `workspace/rules/domain` has the highest reported pressure score at 48.0.

These are attention findings, not boundary or shape violations. No thresholds, exclusions, recipes, rule files, or architecture contracts were changed to suppress them.

### Contract-Change Stop Conditions

- Stop before changing `enclosure.yaml`, recipe manifests, rule thresholds, exclusions, tags, boundary rules, or health reporting semantics to make a check pass.
- Stop if future drift appears outside `workspace/plan`, `workspace/recipe`, or `workspace/sync`.
- Stop if future `enclosure health` reports boundary or shape violations.

### Step 04 Completion

Step 04 distinguishes clean checks, known baseline recipe drift, and attention-level architecture findings without weakening the contract.

## Step 05: Codification Decision

### Route Receipt

- Files read:
  - `AGENTS.md`
  - `.enclosure/plans/CALIBRATION_REPORT.md`
  - `.enclosure/plans/PLAN_STEP_05.md`
  - `.enclosure/rules/INDEX.md`
  - `.enclosure/rules/shared/INDEX.md`
  - `.enclosure/rules/shared/execution/INDEX.md`
  - `.enclosure/rules/shared/execution/CALIBRATION.md`
  - `.enclosure/rules/shared/execution/STEP.md`
  - `.enclosure/rules/local/INDEX.md`
  - `.enclosure/rules/local/execution/INDEX.md`
  - `.enclosure/rules/local/structure/INDEX.md`
  - `.enclosure/rules/local/change/INDEX.md`
- Reason: step 05 is an approved codification decision artifact.
- Stop point: decision report. No contract-change or codification gate has approved edits to `enclosure.yaml`, recipes, local rules, or packaged resources.
- Owner: local rule supplements and packaged guidance only when justified.
- Public seam: this calibration report, with follow-up checks through workspace rules, recipe checks, command-docs tests, and health when codification is approved later.
- Direction: durable observations should narrow existing shared anchors; local rules must not restate shared policy.
- Shape: no rule, recipe, config, docs, or implementation shape changed in this step.
- Verification: post-decision `enclosure health`.

### Decisions

- `keep local`: Route receipt pattern. It is already captured in `shared/execution/CALIBRATION.md` and root `AGENTS.md`; this calibration report is enough for the self-calibration run. Reopen if another module change fails to emit route receipts before edits.
- `defer`: Missing `.enclosure/AGENTS.md`. The active instruction exists in root `AGENTS.md`, and packaged `src/enclosure/resources/AGENTS.md` exists. Reopen if workspace sync is expected to materialize `.enclosure/AGENTS.md` or if a future step requires that exact path.
- `keep local`: Recipe shell command path. `--show` already points to `--shell`, root `--llm` advertises it, packaged module-ladder guidance names it, current workspace rules match packaged guidance, and command-docs validation passes. No further codification is needed.
- `defer`: Baseline recipe drift in `workspace/plan`, `workspace/recipe`, and `workspace/sync`. This is a migration target, not a rule change. Reopen when those modules are approved for shape migration from compact `application.py` to the `application/` package expected by `module-workspace-cli`.
- `keep local`: Attention-level health findings for pressure, coherence, and clusters. They remain reported health signals and should not be suppressed. Reopen if they become blocking violations or if a focused cleanup plan targets one finding.
- `discard`: Contract weakening as a response to failing checks. Steps 01-04 found no reason to relax thresholds, exclusions, tags, recipes, boundaries, or rule schemas.

### Codification Proposals

No codification is applied in this step. If approved later, the narrowest candidates are:

- Add a local execution supplement under `.enclosure/rules/local/execution/` only if repeated calibration work needs project-specific receipt timing beyond `shared/execution/CALIBRATION.md`.
- Add a local structure or migration note under `.enclosure/rules/local/structure/` only if the three baseline drift modules are intentionally kept in legacy `application.py` shape instead of migrated.
- Update sync-carried agent instructions only if `.enclosure/AGENTS.md` becomes an expected generated file rather than a step-input typo or root-level instruction.

### Final Calibration State

- Codified now: none.
- Deferred: `.enclosure/AGENTS.md` materialization question; legacy `application.py` drift migration; attention-finding cleanup.
- Kept local as one-time observations: route receipt evidence, recipe shell verification, guidance sync confirmation, and health reconciliation.
- Discarded: suppressing or weakening contract checks.

### Step 05 Completion

Step 05 records the codification decisions and stops before unapproved contract edits.
