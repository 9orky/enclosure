# Step 03: Workflow Integration

## Implementation Tree

```text
src/enclosure/
  features/
    health/
      report/
        domain.py
          class HealthReport
          def HealthReport.to_json_dict(...) -> dict[str, object]
        ui/
          cli.py
            def health_command(...) -> None
    workspace/
      health/
        domain.py
          class WorkspaceHealthReport
          def WorkspaceHealthReport.to_json_dict(...) -> dict[str, object]
        ui/
          cli.py
            def health_command(...) -> None
      rules/
        ui/
          cli.py
            def rules_command(...) -> None
          templates/
            docs.tmpl
            llm.tmpl
      recipe/
        ui/
          cli.py
            def recipe_command(...) -> None
          templates/
            docs.tmpl
            llm.tmpl
  resources/
    AGENTS.md
    copilot-instructions.md
  templates/
    llm.tmpl
docs/
  modules/
    health-report.md
    workspace-health.md
    workspace-rules.md
    workspace-recipe.md
tests/
  ui/
    test_command_docs.py
      def test_documented_enclosure_commands_resolve(...) -> None
      def test_guidance_enclosure_commands_resolve(...) -> None
      def test_workflow_integration_commands_are_documented(...) -> None
```

## Goal

Make enclosure feedback usable in CI, PR review, editor surfaces, and agent handoffs.

## Step Contract

- Inputs: current CLI output options, generated assistant instructions, command docs, health/rules/recipe checks, and repository CI expectations.
- Outputs: stable automation path for core checks, documented CI examples, and synced agent instructions that name pre-change and post-change commands.
- Scope: command docs, generated guidance, existing JSON/report output paths, and examples for automation.
- Out of scope: hosted integrations, GitHub API posting, editor plugin implementation, or new CI service-specific behavior.
- Owner: CLI output formats, generated instructions, and automation documentation.
- Dependency direction: automation examples consume stable command seams; command seams do not depend on one CI provider.

## Execution

1. Inventory which core commands already support human-readable and machine-readable output.
2. Decide the first stable workflow path for CI and agent handoff using existing commands where possible.
3. Update command docs and generated guidance to show pre-change route discovery and post-change verification.
4. Add examples for `enclosure workspace rules`, `enclosure workspace recipe --check`, and `enclosure health` as the default automation loop.
5. Extend command-docs tests so workflow examples remain valid.
6. Stop if a workflow example requires an output format or option that is not implemented; create a follow-up implementation step instead of documenting it.

## Verification

- Run `uv run pytest tests/ui/test_command_docs.py`.
- Run `enclosure workspace rules`.
- Run `enclosure workspace recipe --check`.
- Run `enclosure health`.

## Completion

Complete when docs and generated instructions give teams a validated automation path for checks before review and a clear agent handoff loop after changes.
