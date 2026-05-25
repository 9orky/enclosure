---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define the base rule for any module-shaped folder of program files.
applies_when:
  - The target folder contains program files that should be treated as one owned unit.
  - No stricter feature or layer contract has been established yet.
tags:
  - structure
  - module
  - api
read_directly: false
escalation_paths:
  - FEATURE.md
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
---

# Module

## Required Decisions

- Owner responsibility.
- Public seam.
- Private internals.

## Core Rules

- A module is a folder that owns one coherent responsibility.
- Export only what real consumers need.
- Keep helpers and intermediate types private.
- Add feature or layer constraints only when the repository contract proves them.

## Review Checks

- One owner, narrow seam, no convenience exports.
