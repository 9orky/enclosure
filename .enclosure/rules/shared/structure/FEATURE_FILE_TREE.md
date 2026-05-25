---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define deterministic file-tree growth for a layered module.
applies_when:
  - The layered module has a required or strongly preferred file-tree pattern.
  - New files should be placed according to layer-owned growth rules.
tags:
  - structure
  - file-tree
  - layers
  - onion
read_directly: false
escalation_paths:
  - FEATURE_LAYERS.md
  - ../architecture/BOUNDARIES.md
  - ../change/REFACTORING.md
---

# Layered Or Onion File Tree

## Required Decisions

- Required folders or root files.
- Owning layer for each new file.
- Public seams to preserve.

## Core Rules

- Grow the tree from ownership and layer direction, not convenience.
- Place new files in their owning layer first.
- Keep public seams stable while internals change.
- Add branches only when the layer model requires them.

## Review Checks

- File placement follows ownership.
- Public seams stay minimal.
