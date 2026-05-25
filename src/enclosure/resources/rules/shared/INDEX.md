---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route canonical shared rules to the shallowest category branch that fits the task.
applies_when:
  - The task needs reusable packaged guidance.
tags:
  - shared
  - routing
  - rules
entrypoint: true
read_strategy: progressive
read_directly: true
child_paths:
  - structure/INDEX.md
  - architecture/INDEX.md
  - change/INDEX.md
  - execution/INDEX.md
  - verification/INDEX.md
---

# Shared Rules

## Use This Branch When

- You need reusable guidance before consulting a repository-local profile.

## Stop Or Descend

- Stop here if the task is already clear.
- Read one branch only: the shallowest branch that matches the current uncertainty.
- Classify structure before applying architecture, change, or verification rules.
- After shared guidance is chosen, use the repository-local profile for concrete
  names, paths, and conventions.

## Architecture Mapping

- Architecture rules rely mostly on glob patterns.
- `architecture.root` maps compact patterns onto real source paths.
- Example: with `architecture.root: src/enclosure/features`, `*/*/ui` means
  `src/enclosure/features/*/*/ui`; full paths still work.
- Best trick: define tags as small reusable globs, then write boundaries in terms of those anchors.
- Keep patterns architecture-sized: describe capabilities, modules, layers, and
  seams instead of long filesystem boilerplate.

## Branches

- [structure/INDEX.md](structure/INDEX.md): classify a target as a module, feature module, or layer
- [architecture/INDEX.md](architecture/INDEX.md): ownership, boundary, and dependency direction
- [change/INDEX.md](change/INDEX.md): rules for reshaping or replacing existing implementation
- [execution/INDEX.md](execution/INDEX.md): execution artifacts
- [verification/INDEX.md](verification/INDEX.md): testing and proof rules for validating behavior

## Review Checks

- The next read is explicit and minimal.
- The local profile is used only after the shared branch is known.
