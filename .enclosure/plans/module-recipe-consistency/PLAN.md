# Module Recipe Consistency

Status: In Progress

## File Tree

```text
.enclosure/
  enclosure.yaml
  recipes/
  plans/
    module-recipe-consistency/
      PLAN.md
      PLAN_STEP_01.md
      PLAN_STEP_02.md
      PLAN_STEP_03.md
      PLAN_STEP_04.md
      PLAN_STEP_05.md
      PLAN_STEP_06.md

src/enclosure/features/
  pattern/
  workspace/
  architecture/
  health/
```

## Goal

Make mapped feature modules consistently match a small set of reusable local
recipes. The work should reduce recipe drift, remove shape violations, and avoid
creating one-off archetypes or premature shared packages.

Current bench command:

```bash
uv run enclosure workspace recipe --bench-all --html .enclosure/.cache/warp-all.html
```

Current result:

- 15 mapped modules.
- 5 recipe roles.
- 12 modules with warp.
- 5 forbidden residue files.
- 33 slot-growth files.
- 15 content-weight findings.
- Overall classification: `unstable`.

Decision: do not add a new shared package or a new full module archetype now.
The strongest signals are stale mappings, legacy compact modules, optional
argument violations, symbol imports, and a few oversized owned files.

## Phases

1. Normalize recipe contracts.
   Step doc: `PLAN_STEP_01.md`.
   Status: Complete.
   Outcome: recipes express the intended small set of reusable module shapes.

2. Refactor `pattern/fit`.
   Step doc: `PLAN_STEP_02.md`.
   Status: Complete.
   Outcome: `pattern/fit` matches the normalized `pattern-module` shape.

3. Refactor workspace CLI application slots.
   Step doc: `PLAN_STEP_03.md`.
   Status: Complete.
   Outcome: `workspace/plan` and `workspace/sync` match
   `module-workspace-cli`.

4. Fix shape violations.
   Step doc: `PLAN_STEP_04.md`.
   Status: Complete.
   Outcome: optional-argument and same-domain symbol-import findings are gone.

5. Split oversized owned internals.
   Step doc: `PLAN_STEP_05.md`.
   Outcome: `workspace/recipe` remains on its current recipe while heavy owned
   internals become smaller.

6. Verify and reassess.
   Step doc: `PLAN_STEP_06.md`.
   Outcome: drift, shape, health, and focused tests confirm the new baseline.

## Acceptance

Required commands:

```bash
uv run enclosure workspace recipe --check
uv run enclosure workspace recipe --drifts
uv run enclosure workspace recipe --bench-all --html .enclosure/.cache/warp-all.html
uv run enclosure architecture shape
uv run enclosure architecture health
uv run pytest tests/functional/test_workspace_recipe_cli.py tests/functional/test_workspace_sync_cli.py tests/functional/test_workspace_rules_cli.py
```

Expected final state:

- Recipe drift is clean for `pattern/fit`, `workspace/plan`, and
  `workspace/sync`.
- Shape violations are 0.
- Boundary violations remain 0.
- The recipe set remains small: existing archetypes plus reusable fragments.

## Open Questions

- Should `architecture/map` and `architecture/pressure` eventually move to
  `module-domain-package-cli` because their `domain.py` files are large?
- Should `workspace/recipe/ui/bench_html.py` become a package if HTML reporting
  keeps growing?
- Should recipe bench content-weight thresholds become configurable later, or
  remain internal heuristics?
