---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: starter_files
discovered_from:
  - architecture.root
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
  - MODULE_LADDER.md
---

# Local File Tree

Reference the matching recipe before adding or reshaping files.

## Rules

- Prefer compact rendered layer files for `domain`, `infrastructure`,
  `application`, and `ui` responsibilities.
- Add only the rendered files whose responsibilities exist.
- The configured module API path is the public module seam.
- Keep file shape aligned with [SHAPE.md](SHAPE.md).
- Use [MODULE_LADDER.md](MODULE_LADDER.md) when a recipe shape grows from a file slot into a package slot.
- Leave legacy layer folders in place until that module is intentionally refactored.

## Checks

- No empty scaffold file is added just to complete a pattern.
- Verification prefers the public seam.
