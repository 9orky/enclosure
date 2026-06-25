---
doc_class: execution
rule_kind: execution
scope: local
generated_by: agent
validation_version: 1
profile_kind: workflow
discovered_from:
  - architecture.root
narrows_paths:
  - ../../shared/execution/STAGE_LOOP.md
audience: agent
purpose: Record local workspace plan stage-loop order after shared stage-loop rules are in scope.
applies_when:
  - Shared stage-loop guidance is already in scope.
  - The work creates or refactors a feature module in this repository.
tags:
  - local
  - execution
  - workspace-plan
  - stage-loop
  - layers
stage: stage_loop
same_artifact_family: execution
read_directly: false
tightens_paths:
  - ../../shared/execution/STAGE_LOOP.md
escalation_paths:
  - ../structure/FEATURE_LAYERS.md
---

# Local Stage Loop

## Rules

- Use `workspace plan` commands for every stage artifact; do not manage
  independent local execution files.
- Keep projected artifacts under `.enclosure/plans/<slug>/`.
- Shape feature-module stages around compact rendered layer files for `domain`,
  `infrastructure`, `application`, and `ui`.
- Within a stage artifact, order layer work from inner to outer according to the
  configured dependency direction.
- Omit responsibilities the module does not need.
- UI stage content consumes the shared current-workspace SSOT; do not add UI
  options for alternate project roots or architecture config paths.
- Schedule package seam updates after the files they expose exist.
- Prefer verification through functional CLI commands only.

## Checks

- No ad hoc execution artifact exists outside `.enclosure/plans/<slug>/`.
- The stage artifact matches `workspace plan agent` output.
- Dependencies point only to completed or explicitly staged earlier layers.
- Verification uses a public seam when practical.
