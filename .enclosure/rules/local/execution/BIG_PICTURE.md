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

- Plan around compact module files: `domain.py`, `infrastructure.py`, `application.py`, `ui.py`.
- Phase order is `domain -> infrastructure -> application -> ui`.
- Omit phases for responsibilities the module does not need.
- UI phases consume the shared current-workspace SSOT; do not plan UI options
  for alternate project roots or architecture config paths.
- Schedule package seam updates after the files they expose exist.

## Checks

- Phases match files and owners.
- Verification uses a public seam when practical.
