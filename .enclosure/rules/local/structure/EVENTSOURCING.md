---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: eventsourcing
discovered_from:
  - ../../../pyproject.toml
  - ../../../src/enclosure/features/workspace/plan
  - https://eventsourcing.readthedocs.io/en/stable/
narrows_paths:
  - ../../shared/structure/FEATURE_LAYERS.md
audience: agent
purpose: Record how this repository uses the Python eventsourcing package across local layers.
applies_when:
  - The target module imports from `eventsourcing`.
  - The target is `features/workspace/plan`.
  - A new feature needs event-sourced state, projections, or event-driven process runners.
tags:
  - local
  - layers
  - eventsourcing
  - event-store
read_directly: false
tightens_paths:
  - ../../shared/structure/FEATURE_LAYERS.md
escalation_paths:
  - ../../shared/architecture/DEPENDENCIES.md
---

# Local Eventsourcing

## Rules

- Use <https://eventsourcing.readthedocs.io/en/stable/> as package SSOT; no
  `llms.txt` or `llms-full.txt` endpoint was found.
- Read `topics/domain.html`, `application.html`, `persistence.html`,
  `projection.html`, and `system.html` before changes.
- `domain` owns `Aggregate`, nested events, event data, and transitions.
- `application` owns the feature `Application` subclass, commands, queries,
  repository access, `save()`, notification-log reads, and mapper conversion.
- `infrastructure` owns persistence env, database paths, SQLite setup, and
  projection stores.
- `ui` calls application seams only; it does not build persistence, runners, or
  recorders.
- Workspace plan state lives in events; markdown files are projections.
- Keep CLI commands finite. Long-lived system/projection runners need explicit
  start and stop ownership.

## Checks

- `workspace/plan/domain/plan.py` owns the aggregate.
- `workspace/plan/application/event_store.py` owns the `Application` subclass.
- `workspace/plan/infrastructure/persistence.py` owns SQLite configuration.
- Long-running event work has a lifecycle seam and concurrency verification.
