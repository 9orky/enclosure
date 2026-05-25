---
doc_class: policy
rule_kind: policy
scope: local
audience: agent
purpose: Record local package seam preferences.
applies_when:
  - Shared module guidance is already in scope.
tags:
  - local
read_directly: false
tightens_paths:
  - ../../shared/structure/MODULE.md
---

# Local Module

## Rules

- Package root is the public seam.

## Checks

- Public imports are intentional.
