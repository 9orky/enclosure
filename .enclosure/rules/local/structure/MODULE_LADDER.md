---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: module_ladder
discovered_from:
  - ../../../.enclosure/recipes/
narrows_paths:
  - ../../shared/structure/MODULE_LADDER.md
audience: agent
purpose: Record this repository's local recipe slots after shared module-ladder rules are in scope.
applies_when:
  - The shared module-ladder rule is already in scope.
  - A recipe or drift check refers to this repository's module shapes.
tags:
  - local
  - recipes
  - module-ladder
read_directly: false
tightens_paths:
  - ../../shared/structure/MODULE_LADDER.md
---

# Local Module Ladder

## Rules

Use these repository recipe slots and rungs when shared module-ladder rules are
already in scope.

## Local Slots

This repository commonly uses these recipe slots:

- `application`: orchestration or command/query entrypoints.
- `domain`: local data, rules, policy, report, or exception types.
- `infrastructure`: adapters, loading, filesystem, config, or external access.
- `ui`: CLI and presentation templates.

These names are local recipe slots. They do not make layered architecture a
global recipe requirement.

## Rungs

- Prefer fixed slot fragments plus `includes` over new archetypes for every
  slot combination.
- `file`: require the rendered slot file; forbid the rendered slot container.
- `package`: require the rendered package seam; forbid the rendered slot file;
  allow private internals.
- `split-files`: require the rendered package seam plus declared child files.
- `split-packages`: require the rendered package seam plus declared child packages.

## Checks

- Recipe drift should be clean for mapped modules.
- Extra files under declared package slots are not drift.
- Extra root files outside declared slots remain drift.
- Recipe bench HTML is an observed artifact, not a source file. If generated,
  it must use a real report path such as `.enclosure/.cache/reports/<name>.html`
  or `/tmp/<name>.html`; command flags like `--help` are never valid output
  filenames.
