---
plan_id: planning-workflow
epic_id: schema-contract-verification
title: Schema Contract Verification Stories
status: dry-run
stage: epics
source: event_store
generated_from: eventsourcing projection
sync_policy: projection
managed_files:
  - EPIC.md
  - USER_STORIES.md
  - SCHEMAS.md
  - flows.mermaid
  - uml.mermaid
  - tree.mermaid
stories:
  - id: parse-planned-contracts
    title: Parse planned Mermaid contracts
    status: candidate
  - id: derive-actual-schemas
    title: Derive actual schemas through modwire
    status: candidate
  - id: report-contract-drift
    title: Report contract drift to agents
    status: candidate
---

# User Stories

## parse-planned-contracts

As the planner, I want to parse planned Mermaid files so that diagrams become
machine-checkable contracts.

Acceptance criteria:

- `tree.mermaid` produces an expected file list.
- `uml.mermaid` produces expected classes, methods, properties, and relations.
- `flows.mermaid` produces expected use-case nodes with file and class targets.

## derive-actual-schemas

As the verifier, I want to query actual implementation structure through modwire
so that the codebase can be compared with the plan.

Acceptance criteria:

- Actual files can be listed for the planned scope.
- Actual symbols can be mapped back to source files.
- Actual schema output can be normalized into the same comparison model as the
  planned contracts.

## report-contract-drift

As an agent, I want precise drift reports so that I can repair code according to
the plan instead of guessing.

Acceptance criteria:

- Missing planned files are reported.
- Unexpected files are reported.
- Missing or mismatched classes, properties, and methods are reported.
- Reports include suggested repair targets.
