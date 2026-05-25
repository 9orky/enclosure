---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Govern seam selection, test scope, and assertion quality.
applies_when:
  - The task needs tests or another proof of behavior.
tags:
  - verification
  - testing
read_directly: false
escalation_paths:
  - ../architecture/BOUNDARIES.md
  - ../architecture/DEPENDENCIES.md
---

# Testing

## Required Decisions

- Seam under test.
- Smallest proving scope.
- Behavior to assert.

## Core Rules

- Prefer the highest valid seam with clear behavioral signal.
- Test modules directly only when they own the seam.
- Do not add test-only production seams.
- Assert behavior and contract, not private mechanics.

## Review Checks

- Seam, scope, and assertions prove behavior without test-only production API.
