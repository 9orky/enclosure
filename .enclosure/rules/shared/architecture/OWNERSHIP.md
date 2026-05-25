---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Decide the owning enclosure for a responsibility before implementation or refactoring.
applies_when:
  - The task touches code that could belong to more than one feature, module, or layer.
tags:
  - architecture
  - ownership
read_directly: false
escalation_paths:
  - BOUNDARIES.md
  - DEPENDENCIES.md
---

# Ownership

## Required Decisions

- Owning enclosure.
- Owning module.
- Owning layer, when layered.

## Core Rules

- One responsibility has one owner.
- Choose the smallest owner that can hold the policy cleanly.
- Split ownership only at an explicit seam.
- Legacy location is evidence, not authority.

## Review Checks

- Owner is explicit and does not widen the API.
