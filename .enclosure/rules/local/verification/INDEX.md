---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route local verification supplements after shared verification guidance.
applies_when:
  - Shared verification guidance is already in scope.
  - Tests or proof seams need repository-local constraints.
tags:
  - local
  - verification
  - routing
read_directly: false
tightens_paths:
  - ../../shared/verification/INDEX.md
entrypoint: true
read_strategy: progressive
child_paths:
  - TESTING.md
---

# Local Verification

## Use This Branch When

- Shared verification rules are already in scope.
- A task creates, changes, reviews, or runs tests for this repository.

## Stop Or Descend

- Read [TESTING.md](TESTING.md) for the repository's functional CLI-only test policy.
- Stop when shared verification rules already decide the case.

## Review Checks

- Shared verification guidance is already in scope.
- Local test policy is applied before adding or editing tests.
