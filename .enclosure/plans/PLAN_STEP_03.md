# Step 03: Guidance Sync Calibration

## Implementation Tree

```text
.enclosure/
  plans/
    PLAN.md
    PLAN_STEP_03.md
  rules/shared/structure/MODULE_LADDER.md
src/enclosure/
  resources/
    AGENTS.md
    rules/shared/structure/MODULE_LADDER.md
  templates/
    llm.tmpl
  features/workspace/sync/
    application.py
      update_project()
    domain.py
      Workspace.plan_update()
    infrastructure.py
      FileRepository.load(...)
tests/ui/
  test_command_docs.py
```

## Goal

Verify upgraded workspaces learn about agent-facing recipe shell preview after sync/update through the guidance surfaces agents already read.

## Step Contract

- Inputs: root `--llm` guidance, packaged shared rules, workspace sync update behavior, command docs validation.
- Outputs: synced guidance that advertises `enclosure workspace recipe <name> <path> --shell` without requiring agents to infer granular flag combinations.
- Scope: guidance discoverability and sync-carried packaged resources.
- Out of scope: changing sync overwrite policy, adding new sync commands, or editing local project config.
- Owner: packaged resources under `src/enclosure/resources` and guidance templates under `src/enclosure/templates`.
- Dependency direction: packaged resources flow into `.enclosure/` through sync; local rules narrow shared guidance after update.

## Execution

1. Confirm root `enclosure --llm` guidance names `--shell` in the recipe workflow.
2. Confirm packaged shared `MODULE_LADDER.md` names `--shell`.
3. Confirm current workspace `.enclosure/rules/shared/structure/MODULE_LADDER.md` matches the packaged guidance when self-calibrating this repo.
4. Validate command examples through the command-docs test surface.
5. Stop if a synced workspace would only discover `--shell` through low-level `--help`.

## Verification

- Run `pytest tests/ui/test_command_docs.py`.
- Run `enclosure workspace rules`.
- If sync behavior changes later, run focused workspace sync functional tests before accepting the phase.

## Completion

Incomplete until the root LLM route, packaged module-ladder rule, and recipe command docs all expose `--shell` as the simple agent path.
