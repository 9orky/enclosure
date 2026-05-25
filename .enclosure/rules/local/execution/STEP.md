---
doc_class: execution
rule_kind: execution
scope: local
generated_by: agent
validation_version: 1
profile_kind: workflow
discovered_from:
  - ../../../src/enclosure/features/architecture/boundaries/
narrows_paths:
  - ../../shared/execution/STEP.md
audience: agent
purpose: Record local step order after shared step workflow rules are in scope.
applies_when:
  - Shared step guidance is already in scope.
  - An approved phase for a feature module is being executed.
tags:
  - local
  - execution
  - step
  - layers
stage: step
same_artifact_family: execution
read_directly: false
tightens_paths:
  - ../../shared/execution/STEP.md
escalation_paths:
  - ../structure/FEATURE_LAYERS.md
---

# Local Step

## Rules

- Keep each step owned by one file/layer.
- Execute in approved order: `domain -> infrastructure -> application -> ui`.
- Do not reach forward into a later layer to finish an earlier step.
- When the step reaches UI, use the shared current-workspace SSOT instead of
  adding or forwarding alternate project-root/config inputs.
- Add `__init__.py` and Typer app wiring as soon as they can honestly expose completed behavior.
- Prefer verification through public CLI/module seams.

## Checks

- Step matches the approved phase.
- Dependencies point only to completed earlier layers.
