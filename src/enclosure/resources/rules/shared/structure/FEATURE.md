---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define stricter ownership and boundary expectations for a feature module.
applies_when:
  - The module owns one user-visible or business capability.
  - Feature boundaries matter to placement, API shape, or dependency control.
tags:
  - structure
  - feature
  - boundary
read_directly: false
escalation_paths:
  - FEATURE_LAYERS.md
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
---

# Feature Module

## Required Decisions

- Capability.
- Public seam.
- Allowed cross-feature collaboration.

## Core Rules

- A feature is a module that owns a capability.
- Keep cross-feature access narrow and seam-based.
- Do not turn adjacency into shared ownership.
- Feature status does not justify a wider API.

## Review Checks

- Capability and seam are explicit.
- Cross-feature access stays narrow.
