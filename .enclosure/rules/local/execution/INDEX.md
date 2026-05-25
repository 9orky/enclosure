---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route local execution supplements after shared execution guidance.
applies_when:
  - Shared execution guidance is already in scope.
  - Repository discovery has identified repo-specific execution order or seam-timing decisions.
tags:
  - local
  - execution
  - routing
read_directly: false
tightens_paths:
  - ../../shared/execution/INDEX.md
entrypoint: true
read_strategy: progressive
child_paths:
  - BIG_PICTURE.md
  - STEP.md
---

# Local Execution

## Use This Branch When

- Shared execution rules are already in scope.
- Phase order, step order, or seam timing needs local detail.

## Stop Or Descend

- Read [BIG_PICTURE.md](BIG_PICTURE.md) for local planning order.
- Read [STEP.md](STEP.md) for local implementation order.
- Stop when shared execution rules are enough.

## Review Checks

- Shared execution guidance is already in scope.
- Local artifact matches the current stage.
