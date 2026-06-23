---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: layers
discovered_from:
  - architecture.root
narrows_paths:
  - ../../shared/structure/FEATURE_LAYERS.md
audience: agent
purpose: Record the repository's layer meanings after shared layered guidance is in scope.
applies_when:
  - The shared layered-feature rule is already in scope.
  - The target is a new or refactored feature module.
tags:
  - local
  - layers
  - dependencies
read_directly: false
tightens_paths:
  - ../../shared/structure/FEATURE_LAYERS.md
escalation_paths:
  - FEATURE_FILE_TREE.md
  - ../../shared/architecture/DEPENDENCIES.md
---

# Local Layers

- `domain`: config models, report types, local exceptions; no app or IO imports.
- `infrastructure`: adapters and loading; may import domain types.
- `application`: use-case orchestration; may import domain and infrastructure seams.
- `ui`: command/presentation composition; may import application and public domain errors/types.

## Rules

- Use only these layer names for governed modules.
- Prefer one rendered file per layer.
- Split a layer into a folder only after stable internal responsibilities appear.
- Direction is `ui -> application -> infrastructure -> domain`.
- `application` may use domain types directly.
- UI uses the shared current-workspace SSOT; do not forward alternate roots or config paths.
- Construct concrete collaborators explicitly; do not hide same-scope defaults behind `None`.
- Keep bootstrap helpers at composition seams unless they form a real service.
- Do not introduce a new layer name without changing the rules first.

## Checks

- Domain is independent; UI does not import infrastructure.
- Public seams are explicit and small.
