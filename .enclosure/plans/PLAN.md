# Enclosure Self-Calibration Plan

## File Tree

```text
.enclosure/
  enclosure.yaml
  plans/
    PLAN.md
  recipes/
  rules/
    INDEX.md
    local/
    shared/
src/enclosure/
  features/
    architecture/
    health/
    workspace/
  resources/
tests/
```

## Goal

Use enclosure to calibrate this repository against its own contract before further feature work. The work should prove that the current rules, recipes, generated guidance, and health checks give an agent enough signal to discover the right route, preview recipe-shaped modules, detect drift, and verify changes without relying on memory or ad hoc conventions.

## Execution Frame

- Owner: workspace contract and recipe/tooling surfaces in `src/enclosure/features/workspace`.
- Public seam: CLI commands and generated `.enclosure/` contract surfaces.
- Direction: rules and recipes guide agents; implementation conforms to them; failed checks trigger implementation fixes before contract changes.
- Shape: prefer existing compact module or declared recipe shapes; do not introduce a new module unless the calibration proves one is needed.
- Verification: highest practical seam is the CLI plus workspace/rule/recipe/health checks.

## Phases

### Phase 1: Route And Contract Calibration

- Objective: confirm the minimal rule route an agent should read before editing this repository.
- Owner: `.enclosure/rules` and `.enclosure/enclosure.yaml`.
- Inputs: shared/local execution rules, structure rules, architecture contract, current AGENTS instruction.
- Outputs: confirmed route receipt pattern and any explicit gaps in first-read guidance.
- Acceptance: route names files read, reason, stop point, focused checks, and post-change `enclosure health`.

### Phase 2: Recipe Shell Calibration

- Objective: prove recipe shell preview is discoverable and useful as the module-shape oracle.
- Owner: `workspace/recipe` command and `.enclosure/recipes`.
- Inputs: `workspace.recipe.roles_map`, recipe manifests, `--show`, `--shell`, and `--drifts`.
- Outputs: documented command path for agents to list, inspect, shell-preview, and drift-check recipe-shaped modules.
- Acceptance: `enclosure workspace recipe --show` points to `--shell`; `--shell` displays rendered tree and skeleton content without writing files; existing drift remains mechanical and named.

### Phase 3: Guidance Sync Calibration

- Objective: verify upgraded workspaces learn about new agent-facing commands after sync/update.
- Owner: packaged resources under `src/enclosure/resources` and generated instruction/guidance templates.
- Inputs: root `--llm`, packaged shared rules, workspace sync update behavior.
- Outputs: synced guidance that advertises the simple command path instead of requiring agents to infer flag combinations.
- Acceptance: `enclosure workspace sync update` would carry the relevant rule guidance; command examples pass docs validation.

### Phase 4: Health And Drift Reconciliation

- Objective: separate actionable regressions from known baseline attention findings.
- Owner: workspace health and architecture health reports.
- Inputs: `enclosure workspace rules`, `enclosure workspace recipe --check`, `enclosure workspace recipe --drifts`, `enclosure health`.
- Outputs: concise reconciliation of pass/fail checks, known recipe drift, and attention-level architecture findings.
- Acceptance: rules and recipes pass; boundaries and shape have 0 violations; known drift or attention findings are reported without weakening the contract.

### Phase 5: Codification Decision

- Objective: decide whether calibration discoveries should become durable local rules, docs, recipes, or no change.
- Owner: local rule supplements and packaged guidance only when justified.
- Inputs: outcomes from phases 1-4.
- Outputs: explicit keep/change/defer decisions for each discovery.
- Acceptance: durable facts are codified narrowly under the matching local/shared anchor; one-off observations stay in the plan or final report.

## Acceptance

- `.enclosure/plans/PLAN.md` exists and remains phase-level only.
- No `PLAN_STEP_0X.md` files exist before phase approval.
- Focused checks run after plan creation:
  - `enclosure workspace rules`
  - `enclosure workspace recipe --check`
  - `enclosure health`
- Any check failure is treated as signal; the contract is not weakened to manufacture a pass.
- The final calibration report names route, owner, seam, direction, shape, verification, drift, and remaining open questions.

## Open Questions

- Should known recipe drift in `workspace/plan`, `workspace/recipe`, and `workspace/sync` become an explicit migration target or remain accepted legacy shape for now?
- Should `--shell` be promoted beyond recipe guidance into the top-level assistant instruction file, or is root `--llm` plus module-ladder guidance enough?
- Should self-calibration produce reusable local execution rules, or should it remain a one-time plan until repeated by another module change?
