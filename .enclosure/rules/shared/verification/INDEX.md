---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route proof and testing questions.
applies_when:
  - The task needs to prove behavior or choose a testing seam.
tags:
  - verification
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - TESTING.md
---

# Verification

## Use This Branch When

- A change needs proof or a test seam.

## Stop Or Descend

- Read [TESTING.md](TESTING.md) for test scope, seam, or assertion guidance.
- Stop when proof strategy is clear.

## Review Checks

- Verification question is explicit.
