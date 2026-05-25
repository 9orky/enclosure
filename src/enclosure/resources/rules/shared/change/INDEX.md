---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route code-change work that reshapes existing implementation.
applies_when:
  - The task changes existing code structure rather than adding a new slice only.
tags:
  - change
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - REFACTORING.md
---

# Change

## Use This Branch When

- Existing implementation must be reshaped.

## Stop Or Descend

- Read [REFACTORING.md](REFACTORING.md) when target design must replace or reshape legacy code.
- Stop for pure new-slice implementation.

## Review Checks

- Use this branch only for structural change work.
