# Step 02: Actionable Health Output

## Implementation Tree

```text
src/enclosure/
  features/
    health/
      report/
        domain.py
          class HealthFinding
          class HealthReport
        application.py
          def build_health_report() -> domain.HealthReport
          def build_health_report_for_top(top: int | None) -> domain.HealthReport
        ui/
          cli.py
            def health_command(...) -> None
          templates/
            report.tmpl
            docs.tmpl
            llm.tmpl
    workspace/
      health/
        domain.py
          class WorkspaceHealthFinding
          class WorkspaceHealthReport
        application.py
          def build_workspace_health_report() -> domain.WorkspaceHealthReport
        ui/
          cli.py
            def health_command(...) -> None
          templates/
            report.tmpl
tests/
  features/
    health/
      report/
        test_functional.py
          def test_root_health_fails_when_workspace_health_has_blocking_findings(...) -> None
          def test_root_health_reports_actionable_next_steps(...) -> None
    workspace/
      health/
        test_functional.py
          def test_workspace_health_reports_broken_fixture_workspace(...) -> None
          def test_workspace_health_classifies_findings_by_actionability(...) -> None
```

## Goal

Turn health output into prioritized next actions without weakening any contract checks.

## Step Contract

- Inputs: root health report, workspace health report, architecture health data, recipe drift output, boundary and shape results, pressure/coherence/clusters findings, and current health tests.
- Outputs: health summaries that classify findings as blockers, baseline drift, attention findings, or suggested investigations.
- Scope: health domain models, report rendering, CLI wording, and focused tests for actionable output.
- Out of scope: changing architecture thresholds, suppressing findings, changing recipe drift detection, or adding a separate remediation engine.
- Owner: root health report and workspace health report surfaces.
- Dependency direction: root health aggregates lower-level reports; lower-level reports do not depend on root health UI wording.

## Execution

1. Inspect current root and workspace health models for severity, blocking status, JSON shape, and rendered output.
2. Define the smallest actionability model needed to separate blockers, baseline drift, attention findings, and suggested follow-up commands.
3. Update root and workspace health rendering so each finding tells the user what kind of action is expected.
4. Preserve nonzero exit behavior for blocking findings and keep attention findings visible.
5. Add tests for one blocker, one drift or baseline-style finding, and one attention-level finding.
6. Stop if actionability requires changing architecture report semantics; split that into a separate approved phase.

## Verification

- Run `uv run pytest tests/features/health/report/test_functional.py tests/features/workspace/health/test_functional.py`.
- Run `enclosure health`.
- Run `enclosure workspace rules`.

## Completion

Complete when health output makes review-blocking and non-blocking findings clear, gives concrete next actions, and preserves existing contract enforcement.
