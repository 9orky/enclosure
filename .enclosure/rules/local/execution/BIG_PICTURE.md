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
  - ../../shared/execution/BIG_PICTURE.md
audience: agent
purpose: Record local planning order after shared workflow rules are in scope.
applies_when:
  - Shared big-picture guidance is already in scope.
  - The work creates or refactors a feature module in this repository.
tags:
  - local
  - execution
  - big-picture
  - layers
stage: big_picture
same_artifact_family: execution
read_directly: false
tightens_paths:
  - ../../shared/execution/BIG_PICTURE.md
escalation_paths:
  - ../structure/FEATURE_LAYERS.md
---

# Local Big Picture

## Rules

- Manage planning documents with `enclosure plan` and `enclosure plan <kebab-slug>`.
- Store planning documents only under `.enclosure/plans/`.
- Use `--show` to preview; use `--force` only after explicit approval.
- Do not create ad hoc `PLAN.md`, `UML.md`, or step files outside `.enclosure/plans/`.
- Plan around compact rendered layer files for `domain`, `infrastructure`,
  `application`, and `ui`.
- Phase order follows configured dependency direction from inner to outer layer.
- Omit phases for responsibilities the module does not need.
- UI phases consume the shared current-workspace SSOT; do not plan UI options
  for alternate project roots or architecture config paths.
- Schedule package seam updates after the files they expose exist.

## Checks

- The plan path is `.enclosure/plans/<kebab-slug>/PLAN.md`.
- Phases match files and owners.
- Verification uses a public seam when practical.
