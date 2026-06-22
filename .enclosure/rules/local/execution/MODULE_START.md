---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: workflow
discovered_from:
  - ../../../src/enclosure/features/
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

- Treat `enclosure architecture health` as the module consistency report, not as
  a simple green/red gate.
- Before coding a module, identify the target realm, module stream, layer set,
  public seam, and closest healthy sibling stream.
- Start from the established boilerplate for that stream shape. Prefer the
  matching `.enclosure/recipes/` manifest and existing sibling files over a new
  file layout.
- Keep module work navigable for human review: compact files, repeated names,
  predictable layer order, and no hidden cross-module shortcuts.
- Use health findings as local rules for the touched stream. Do not broaden the
  task into unrelated shape, pressure, or coherence cleanup.
- Start procedure: run `enclosure architecture health --vv --top -1` or inspect
  the freshest equivalent report, locate the owning stream, compare with a
  nearby consistent sibling, use the mapped recipe for new modules or slots, and
  implement in configured inner-to-outer layer order.
- When a command requires an HTML or report output path, write it to an explicit
  throwaway artifact path such as `.enclosure/.cache/reports/<name>.html` or a
  `/tmp` path. Never use an option token such as `--help`, `--docs`, `--llm`, or
  any other flag as the value for `--html` or another output-path option.

## Checks

- A reviewer can scan the whole module and recognize the same file names,
  exports, command wiring, and dependency direction used by sibling modules.
- New health findings are either absent, scoped to the touched stream, or called
  out explicitly as accepted remaining work.
- The final explanation names the module stream and the focused verification
  command, not only the global health status.
- No root-level report artifact such as `--help` was created by a command that
  expected an output path.
