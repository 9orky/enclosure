---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: shape
discovered_from:
  - ../../../enclosure.yaml
narrows_paths:
  - ../../shared/structure/MODULE.md
audience: agent
purpose: Record this repository's shape flags after shared module rules are in scope.
applies_when:
  - The shared module or feature-file rule is already in scope.
  - A Python file under the governed source tree is being added or changed.
tags:
  - local
  - shape
  - imports
  - signatures
read_directly: false
tightens_paths:
  - ../../shared/structure/MODULE.md
escalation_paths:
  - FEATURE_FILE_TREE.md
---

# Local Shape

`enclosure.yaml` disables numeric size caps; do not invent local class,
function, method, argument, or line-count limits.

## Rules

- Keep signatures explicit: no defaulted function args, method args, or optional class properties.
- Cross-file imports bring in modules through package seams, not individual symbols.
- Do not alias cross-file imports.
- Join imports from the same parent into one statement.

## Checks

- `enclosure architecture shape` passes.
- Imports are module-level, joined, and unaliased.
- Optionality is modeled deliberately, not hidden in defaults or nullable properties.
