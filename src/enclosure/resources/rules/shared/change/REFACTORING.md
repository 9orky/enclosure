---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Govern target-design refactoring and fresh-slice decisions.
applies_when:
  - Existing code must be reshaped toward a clearer target design.
tags:
  - change
  - refactoring
read_directly: false
escalation_paths:
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
  - ../verification/TESTING.md
---

# Refactoring

## Required Decisions

- Target design.
- In-place refactor or fresh slice.
- Verification seam.

## Core Rules

- Let target design lead; legacy layout is weak evidence.
- Use a fresh slice when ownership, boundary, or structure changes materially.
- Keep dual paths only long enough to verify the swap.
- Remove scaffolding after replacement.

## Review Checks

- Target, migration choice, and proof seam are explicit.
