---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: layers
discovered_from:
  - ../../../src/enclosure/features/architecture/boundaries/
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

`architecture/boundaries` and `architecture/clusters` are the model:

- `domain.py`: config models, report types, local exceptions; no app or IO imports.
- `infrastructure.py`: adapters and loading; may import domain types.
- `application.py`: use-case orchestration; may import domain and infrastructure seams.
- `ui.py`: CLI/presentation; may import application and public domain errors/types.

## Rules

- Use only these layer names for governed modules.
- Prefer one file per layer.
- Split a layer into a folder only after stable internal responsibilities appear.
- Direction is `ui -> application -> infrastructure -> domain`.
- `application` may use domain types directly.
- The UI layer must not accept or pass alternate project roots or architecture
  config paths; use the shared SSOT for the current project root and enclosure
  folder, then let lower layers auto-discover config from that workspace.
- Do not inject nullable service objects into a constructor when those objects
  are instantiated in the same place; construct the concrete collaborators
  explicitly instead of hiding default wiring behind `None`.
- Do not use the application layer as a dumping ground for sets of factory
  functions just because a module needs bootstrap helpers; add a real service
  or keep construction at the CLI/composition seam.
- Do not introduce a new layer name without changing the rules first.

## Checks

- Domain is independent; UI does not import infrastructure.
- Public seams are explicit and small.
