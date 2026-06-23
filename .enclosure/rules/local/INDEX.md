---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route repository-local rule supplements after the matching shared branch is already known.
applies_when:
  - The shared branch is already in scope.
  - Repository discovery is complete.
  - The task still needs repository-local narrowing rather than another shared branch.
tags:
  - local
  - routing
  - rules
read_directly: false
tightens_paths:
  - ../shared/INDEX.md
entrypoint: true
read_strategy: progressive
child_paths:
  - structure/INDEX.md
  - change/INDEX.md
  - execution/INDEX.md
  - verification/INDEX.md
---

# Local Rules

## Use This Branch When

- The matching shared branch is already known.
- A project-specific path, layer name, scaffold, or workflow choice is still needed.

## Local Mapping

- Use the configured `architecture.root` as the source of truth for governed modules.
- Write governed module paths relative to that root when possible.
- Use full paths only for code outside the configured architecture root.

## Stop Or Descend

- Read [structure/INDEX.md](structure/INDEX.md) for local seams, layers, or starter files.
- Read [change/INDEX.md](change/INDEX.md) for local fresh-start refactoring rules.
- Read [execution/INDEX.md](execution/INDEX.md) for local phase or step order.
- Read [verification/INDEX.md](verification/INDEX.md) for the local test seam policy.
- Stop when shared rules already decide the case.

## Review Checks

- Shared guidance is already in scope before this branch is opened.
- Local rules add project facts; they do not restate shared policy.
