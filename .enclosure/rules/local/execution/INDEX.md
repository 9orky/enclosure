---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route local execution supplements after shared stage-loop guidance.
applies_when:
  - Shared execution guidance is already in scope.
  - Repository discovery has identified repo-specific stage order or seam-timing decisions.
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
  - MODULE_START.md
  - STAGE_LOOP.md
---

# Local Execution

## Use This Branch When

- Shared execution rules are already in scope.
- Workspace plan stage order or seam timing needs local detail.

## Stop Or Descend

- Read [MODULE_START.md](MODULE_START.md) before starting feature-module code
  or refactoring a module stream.
- Read [STAGE_LOOP.md](STAGE_LOOP.md) for local workspace plan stage-loop order.
- Stop when shared execution rules are enough.

## Review Checks

- Shared execution guidance is already in scope.
- Local artifact matches the active workspace plan stage.
