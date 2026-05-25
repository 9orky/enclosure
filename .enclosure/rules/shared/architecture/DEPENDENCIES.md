---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Decide allowed dependency direction for the current structure.
applies_when:
  - The task adds or changes a dependency between folders, modules, or layers.
tags:
  - architecture
  - dependencies
read_directly: false
escalation_paths:
  - OWNERSHIP.md
  - BOUNDARIES.md
---

# Dependencies

## Required Decisions

- Source.
- Target.
- Valid direction.

## Core Rules

- Make direction explicit when structure matters.
- Depend on seams, not internals.
- Children must not depend on consumers.
- Cycles are forbidden.

## Review Checks

- Direction matches the structure and reaches a seam.
