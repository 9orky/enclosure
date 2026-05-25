---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route repository-local structure supplements for this workspace.
applies_when:
  - Shared structure classification is already known.
  - Repository discovery found local package, feature, layer, or tree conventions.
tags:
  - local
  - structure
  - routing
read_directly: false
tightens_paths:
  - ../../shared/structure/INDEX.md
entrypoint: true
read_strategy: progressive
child_paths:
  - MODULE.md
  - SHAPE.md
  - FEATURE.md
  - FEATURE_LAYERS.md
  - FEATURE_FILE_TREE.md
---

# Local Structure

## Use This Branch When

- Shared module or feature structure is already in scope.
- A local seam, layer name, or starter-file convention is still needed.

## Stop Or Descend

- Read [MODULE.md](MODULE.md) for Python package seams.
- Read [SHAPE.md](SHAPE.md) for local signature and import-shape flags.
- Read [FEATURE.md](FEATURE.md) for feature-root conventions.
- Read [FEATURE_LAYERS.md](FEATURE_LAYERS.md) for the local layer set.
- Read [FEATURE_FILE_TREE.md](FEATURE_FILE_TREE.md) for compact starter files.
- Stop when shared structure rules are enough.

## Review Checks

- Local structure guidance only narrows shared structure.
- Stop at the shallowest local supplement that fits.
