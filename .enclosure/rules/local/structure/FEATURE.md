---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: module_seams
discovered_from:
  - ../../../src/enclosure/features/
narrows_paths:
  - ../../shared/structure/FEATURE.md
audience: agent
purpose: Record this repository's feature-root seam after the shared feature rule is in scope.
applies_when:
  - The shared feature rule is already in scope.
  - The target is under the configured architecture root.
tags:
  - local
  - feature
  - seam
read_directly: false
tightens_paths:
  - ../../shared/structure/FEATURE.md
escalation_paths:
  - FEATURE_LAYERS.md
---

# Local Feature

Use `architecture/boundaries` and `architecture/clusters` as current reference modules.

## Rules

- Feature roots stay small: `__init__.py`, optional `cli.py`, and owned modules.
- Behavior lives in modules such as `architecture/boundaries`, not in the feature root.
- Cross-feature imports use public seams, preferably `__init__.py` or feature `cli.py`.

## Checks

- Feature root exposes only real seams.
- Each module has one owner and purpose.
