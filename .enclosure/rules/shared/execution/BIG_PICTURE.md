---
doc_class: execution
rule_kind: execution
audience: agent
purpose: Define phase-level execution before step files exist.
applies_when:
  - The first execution artifact for the work is being written.
  - Approved phases do not exist yet.
tags:
  - execution
  - big-picture
stage: big_picture
same_artifact_family: execution
read_directly: false
escalation_paths: []
---

# Big Picture

## Required Sections

- `File Tree`
- `Goal`
- `Phases`
- `Acceptance`
- `Open Questions`

## Optional Sections

- `Execution Frame`
- `Strategic Model`

## File Tree Rules

- Put `File Tree` first.
- Name the artifact `PLAN.md`.
- List folders and files only; no signatures.
- If phases name layers, the tree uses the same layer set.

## Phase Rules

- Make `Phases` the center.
- Each phase states objective, owner, inputs, outputs, and acceptance.
- Approved phase order becomes step order.

## Strategic Model Gate

- Add `Strategic Model` only for material business or domain-language change.

## Review Checks

- Tree first, `PLAN.md`, phase-level only.
- Phases map directly to steps.
- Acceptance and open questions are explicit.

## Handoff Checks

- No step files before approval.
- Implementation detail stays out of the big picture.
