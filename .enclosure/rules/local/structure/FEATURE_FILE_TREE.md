---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: starter_files
discovered_from:
  - ../../../src/enclosure/features/architecture/boundaries/
narrows_paths:
  - ../../shared/structure/FEATURE_FILE_TREE.md
audience: agent
purpose: Record the compact feature-module file tree after shared tree rules.
applies_when:
  - The shared layered file-tree rule is already in scope.
  - A new or refactored module follows the current compact module pattern.
tags:
  - local
  - file-tree
  - layers
read_directly: false
tightens_paths:
  - ../../shared/structure/FEATURE_FILE_TREE.md
escalation_paths:
  - FEATURE_LAYERS.md
---

# Local File Tree

Reference shape: `architecture/boundaries`.

## Rules

- Prefer compact root files: `domain.py`, `infrastructure.py`, `application.py`, `ui.py`.
- Add only the files whose responsibilities exist.
- `__init__.py` is the public module seam.
- Keep file shape aligned with [SHAPE.md](SHAPE.md).
- Leave legacy layer folders in place until that module is intentionally refactored.

## Checks

- No empty scaffold file is added just to complete a pattern.
- Verification prefers the public seam.
