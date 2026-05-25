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
purpose: Record this repository's Python package seam after the shared module rule is in scope.
applies_when:
  - The shared module rule is already in scope.
  - The target is an importable Python package in this repository.
tags:
  - local
  - structure
  - module
  - python
read_directly: false
tightens_paths:
  - ../../shared/structure/MODULE.md
escalation_paths:
  - FEATURE.md
---

# Local Module

## Rules

- Package root is the public seam.
- `__init__.py` exports only names used by real consumers.
- Keep root entrypoints such as `cli.py` explicit.
- Cross-file imports bring in modules through package seams, joined and unaliased.

## Checks

- Public imports are intentional; bootstrap code is visible.
- No file reaches across a boundary for individual symbols.
