---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: module_seams
discovered_from:
  - architecture.root
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

Use the configured module map and recipe map as the current reference.

## Rules

- Feature roots stay small: configured public seams and owned modules only.
- Behavior lives in owned modules, not in the feature root.
- Cross-feature imports use configured public seams.

## Checks

- Feature root exposes only real seams.
- Each module has one owner and purpose.
