---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route structural questions about ownership, boundaries, and dependency direction.
applies_when:
  - The task needs placement or boundary guidance before coding or refactoring.
tags:
  - architecture
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - OWNERSHIP.md
  - BOUNDARIES.md
  - DEPENDENCIES.md
---

# Architecture

## Use This Branch When

- Placement, seam, or dependency direction is unclear.

## Stop Or Descend

- Read [OWNERSHIP.md](OWNERSHIP.md) for the owning enclosure.
- Read [BOUNDARIES.md](BOUNDARIES.md) for public seam and private internals.
- Read [DEPENDENCIES.md](DEPENDENCIES.md) for allowed direction.
- Stop when owner, seam, and direction are clear.

## Review Checks

- The next read answers one concrete structural question.
