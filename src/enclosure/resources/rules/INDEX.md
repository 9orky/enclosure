---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Explain the packaged rule corpus and route readers into the shared guidance tree.
applies_when:
  - Starting rule selection for a task or target folder.
  - The agent needs packaged guidance that ships with enclosure.
tags:
  - bootstrap
  - routing
  - rules
entrypoint: true
read_strategy: progressive
read_directly: true
child_paths:
  - shared/INDEX.md
---

# Rules

## Read Order

- Start with [shared/INDEX.md](shared/INDEX.md) for canonical reusable guidance.

## Stop Or Descend

- Stop here if the task does not need branch-specific rules yet.
- Descend into the shared packaged branch when task-specific guidance is needed.
- Prefer the shallowest matching shared branch over deeper specialization.
- Workspace-local project-profile artifacts belong to the generated project contract, not to this packaged rule tree.

## Branches

- [shared/INDEX.md](shared/INDEX.md): canonical reusable rules organized by category

## Review Checks

- The packaged rule corpus routes only to packaged shared guidance.
- The next read is explicit.
- Workspace-local project-profile artifacts are not represented as packaged branches.