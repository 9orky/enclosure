---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route local refactoring supplements after shared change guidance.
applies_when:
  - Shared change guidance is already in scope.
  - The repository needs stricter local fresh-start refactoring rules.
tags:
  - local
  - change
  - refactoring
  - routing
read_directly: false
tightens_paths:
  - ../../shared/change/INDEX.md
entrypoint: true
read_strategy: progressive
child_paths:
  - REFACTORING.md
---

# Local Change

## Use This Branch When

- Shared change rules are already in scope.
- A refactor needs this repository's fresh-start discipline.

## Stop Or Descend

- Read [REFACTORING.md](REFACTORING.md) for module/package replacement work.
- Stop when shared change rules are enough.

## Review Checks

- Shared change guidance is already in scope.
