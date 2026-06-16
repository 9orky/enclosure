# Step 01: First-Run Onboarding

## Implementation Tree

```text
README.md
  Quick Start
src/enclosure/
  resources/
    AGENTS.md
    copilot-instructions.md
  templates/
    llm.tmpl
    docs.tmpl
  features/
    workspace/
      sync/
        ui/
          templates/
            docs.tmpl
            llm.tmpl
      recipe/
        ui/
          templates/
            docs.tmpl
            llm.tmpl
      rules/
        ui/
          templates/
            docs.tmpl
            llm.tmpl
tests/
  ui/
    test_command_docs.py
      def test_documented_enclosure_commands_resolve(...) -> None
      def test_guidance_enclosure_commands_resolve(...) -> None
      def test_first_run_onboarding_path_is_documented(...) -> None
```

## Goal

Make the first useful `enclosure` path obvious for a new user or coding agent.

## Step Contract

- Inputs: current README quick start, `enclosure --llm`, generated agent instructions, workspace sync guidance, recipe preview guidance, rule route guidance, and command docs validation.
- Outputs: one primary onboarding path that covers initialization, contract inspection, route discovery, recipe preview, health checks, and next-action selection.
- Scope: documentation, generated guidance, and command examples for the first-run loop.
- Out of scope: new onboarding command, sync overwrite policy changes, health semantics, or recipe behavior changes.
- Owner: workspace sync guidance, root guidance templates, README quick start, and command docs.
- Dependency direction: generated guidance consumes the existing CLI contract; docs do not invent commands that the CLI cannot validate.

## Execution

1. Compare README quick start, `enclosure --llm`, generated `AGENTS.md`, and workspace command docs for conflicting first-run paths.
2. Define one canonical first-run sequence from repository root: sync/init, inspect contract, route rules, preview recipes, run health, and choose the next task.
3. Update README and generated guidance templates so human docs and agent-facing guidance tell the same story.
4. Add or extend command-docs tests so every command in the onboarding sequence resolves.
5. Stop if the desired onboarding path needs CLI behavior that does not exist yet; record that as a later implementation decision instead of documenting a false path.

## Verification

- Run `uv run pytest tests/ui/test_command_docs.py`.
- Run `enclosure workspace rules`.
- Run `enclosure health`.

## Completion

Complete when README, `enclosure --llm`, and generated agent guidance expose the same first-run loop and the documented commands validate.
