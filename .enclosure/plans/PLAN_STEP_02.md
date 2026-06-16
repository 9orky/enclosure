# Step 02: Recipe Shell Calibration

## Implementation Tree

```text
.enclosure/
  enclosure.yaml
  plans/
    PLAN.md
    PLAN_STEP_02.md
  recipes/
    module-workspace-cli/
    module-report-cli/
src/enclosure/features/workspace/recipe/
  domain.py
    class RecipePreviewStatus
    class RecipePreviewFile
    class RecipeGenerationReport
  application.py
    describe_recipe_generation(...)
    _RecipeGenerationService._plan_preview_files(...)
  ui/
    cli.py
      recipe_command(...)
    templates/
      dry_run_result.tmpl
      recipe_summary.tmpl
      docs.tmpl
      llm.tmpl
tests/features/workspace/recipe/
  test_application.py
  test_functional.py
```

## Goal

Prove recipe shell preview is discoverable and useful as the module-shape oracle before agents generate or hand-write recipe-shaped code.

## Step Contract

- Inputs: `workspace.recipe.roles_map`, recipe manifests, recipe templates, `--list`, `--show`, `--shell`, and `--drifts`.
- Outputs: verified command path for listing, inspecting, shell-previewing, and drift-checking recipe-shaped modules.
- Scope: recipe preview behavior, recipe CLI guidance, and recipe drift signal.
- Out of scope: heuristic normalized content comparison and migration of legacy module shapes.
- Owner: `workspace/recipe` command and `.enclosure/recipes`.
- Dependency direction: CLI/UI consumes application preview reports; application consumes domain preview models and rendered recipe files; recipes remain contract input.

## Execution

1. Run `enclosure workspace recipe --list` to identify available recipe roles.
2. Run `enclosure workspace recipe <name> --show` and confirm it exposes the next `--shell` command.
3. Run `enclosure workspace recipe <name> <path> --shell` and confirm it prints create/skip paths, rendered tree entries, source templates, and skeleton content without writing files.
4. Run `enclosure workspace recipe --drifts` to compare mapped module trees mechanically.
5. Record known drift separately from preview behavior.
6. Stop if shell preview writes files, hides skip reasons, or requires agents to infer flag combinations.

## Verification

- Run recipe application and functional tests for preview models, skip statuses, `--show`, and `--shell`.
- Run `enclosure workspace recipe --check`.
- Run `enclosure workspace recipe --drifts` and record any existing drift without changing the contract.

## Completion

Incomplete until `--show` points to `--shell`, `--shell` proves the rendered module shell without writes, and baseline drift is named as mechanical signal.
