---
doc_class: policy
rule_kind: policy
scope: local
audience: agent
purpose: Tighten refactoring into a fresh-start replacement workflow for this repository.
applies_when:
  - Shared refactoring guidance is already in scope.
  - Existing implementation is being replaced by a newly owned module or package.
tags:
  - local
  - change
  - refactoring
  - fresh-start
read_directly: false
tightens_paths:
  - ../../shared/change/REFACTORING.md
escalation_paths:
  - ../../shared/architecture/OWNERSHIP.md
  - ../../shared/architecture/BOUNDARIES.md
---

# Local Refactoring

Use `architecture/boundaries` as the preferred shape for new or refactored modules.

## Rules

- Name the new owner, old path, and verification seam before moving code.
- Treat module refactors as fresh implementations of current rules.
- Use legacy code only to preserve observable behavior.
- Do not import from, re-export, or wrap the old module as a shortcut.
- Keep side-by-side code temporary.
- Prefer functional tests through the CLI or public module seam.

## Checks

- New module follows current local structure.
- Swap point is explicit and verified.
