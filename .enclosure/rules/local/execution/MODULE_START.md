---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: workflow
discovered_from:
  - architecture.root
  - ../../../.enclosure/enclosure.yaml
narrows_paths:
  - ../../shared/execution/INDEX.md
audience: agent
purpose: Use architecture health as the module consistency index before coding a feature module.
applies_when:
  - Starting new feature-module code in this repository.
  - Refactoring an existing feature-module stream.
  - Deciding which boilerplate, layer set, or sibling module shape to copy.
tags:
  - local
  - execution
  - module-start
  - architecture-health
read_directly: false
tightens_paths:
  - ../../shared/execution/INDEX.md
escalation_paths:
  - ../structure/FEATURE_FILE_TREE.md
  - ../structure/FEATURE_LAYERS.md
  - ../structure/MODULE.md
---

# Local Module Start

## Rules

- Before coding a module, identify the target realm, module stream, layer set,
  public seam, and closest healthy sibling stream.
- Treat `enclosure architecture health` as a consistency report, not a green/red gate.
- Prefer the mapped recipe and sibling files over a new layout.
- Keep module work compact, navigable, and free of hidden cross-module shortcuts.
- Use touched-stream health findings locally; do not broaden into unrelated cleanup.
- Start from the freshest architecture-health report, compare a nearby healthy
  sibling, use the mapped recipe, and implement inner-to-outer.
- HTML/report output paths must be explicit throwaway paths under
  `.enclosure/.cache/` or `/tmp`; option flags are never output filenames.

## Checks

- Reviewers can recognize sibling file names, seams, wiring, and direction.
- New health findings are absent, scoped, or explicitly accepted.
- The final summary names the stream and focused verification.
- No root-level artifact was created from an option flag.
