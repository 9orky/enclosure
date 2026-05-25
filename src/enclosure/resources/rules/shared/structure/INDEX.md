---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Classify the target folder at the shallowest structural level that fits.
applies_when:
  - The task needs structural rules for a code folder or package.
  - The agent must decide whether deeper specialization is required.
tags:
  - structure
  - routing
  - module
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - MODULE.md
  - FEATURE.md
  - FEATURE_LAYERS.md
  - FEATURE_FILE_TREE.md
---

# Structure

## Use This Branch When

- A code folder needs classification before placement or change rules.

## Stop Or Descend

- Read [MODULE.md](MODULE.md) for any owned folder of program files.
- Then read [FEATURE.md](FEATURE.md) only for capability-owned modules.
- Then read [FEATURE_LAYERS.md](FEATURE_LAYERS.md) only when layer direction matters.
- Then read [FEATURE_FILE_TREE.md](FEATURE_FILE_TREE.md) only when file placement is constrained.

## Review Checks

- Stop at the first rule that answers the structural question.
- Do not assume feature, layer, or tree constraints without evidence.
