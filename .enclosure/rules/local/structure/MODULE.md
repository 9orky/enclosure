---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: module_seams
discovered_from:
  - ../../../src/enclosure/
  - ../../../pyproject.toml
narrows_paths:
  - ../../shared/structure/MODULE.md
audience: agent
purpose: Record this repository's module seam rule after the shared module rule is in scope.
applies_when:
  - The shared module rule is already in scope.
  - The target is an importable module unit in this repository.
tags:
  - local
  - structure
  - module
read_directly: false
tightens_paths:
  - ../../shared/structure/MODULE.md
escalation_paths:
  - FEATURE.md
---

# Local Module

## Rules

- Package root is the public seam.
- The configured module API seam exports only names used by real consumers.
- Keep root entrypoints explicit.
- Cross-file imports bring in modules through configured seams, joined and unaliased.

## Checks

- Public imports are intentional; bootstrap code is visible.
- No file reaches across a boundary for individual symbols.
