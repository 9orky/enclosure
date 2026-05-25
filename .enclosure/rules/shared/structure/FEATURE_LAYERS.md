---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define allowed layers and dependency direction inside a layered module.
applies_when:
  - The module has explicit layers that constrain placement.
  - Dependency direction must be enforced inside the module.
tags:
  - structure
  - layers
  - onion
  - dependencies
read_directly: false
escalation_paths:
  - FEATURE_FILE_TREE.md
  - ../architecture/DEPENDENCIES.md
  - ../architecture/OWNERSHIP.md
---

# Layered Or Onion Module

## Required Decisions

- Allowed layers or rings.
- Dependency direction.
- Owning layer for each touched responsibility.

## Core Rules

- Layers exist to constrain placement and dependency direction.
- Outer layers may depend inward through seams; inner layers must not depend outward.
- Each responsibility has one owning layer.
- Project-local names may vary, but direction and seams must stay strict.

## Review Checks

- Layer names, owner, and direction are explicit.
- No cross-layer shortcut bypasses the seam.
