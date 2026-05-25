---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Decide the public seam and protect private internals.
applies_when:
  - The task may change what is exposed or how callers reach the code.
tags:
  - architecture
  - boundaries
read_directly: false
escalation_paths:
  - OWNERSHIP.md
  - DEPENDENCIES.md
---

# Boundaries

## Required Decisions

- Public boundary.
- Public seam.
- Private internals.

## Core Rules

- Expose only what real callers need.
- Keep helpers, policies, and intermediate models private.
- Do not widen APIs to avoid local composition.
- Do not deep-import across a boundary.

## Review Checks

- Seam is explicit, narrow, and not bypassed.
