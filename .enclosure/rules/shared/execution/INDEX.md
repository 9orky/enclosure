---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route execution work between calibration, workspace plan stages, and contract diagrams.
applies_when:
  - The task needs execution guidance before or during coding.
tags:
  - execution
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - CALIBRATION.md
  - STAGE_LOOP.md
  - CONTRACT_DIAGRAMS.md
---

# Execution

## Use This Branch When

- Work needs a workspace plan stage, implementation contract, or contract diagram.

## Stop Or Descend

- Read [CALIBRATION.md](CALIBRATION.md) when the project contract is not already clear.
- Read [STAGE_LOOP.md](STAGE_LOOP.md) when drafting, advancing, or recovering a workspace plan.
- Read [CONTRACT_DIAGRAMS.md](CONTRACT_DIAGRAMS.md) when a stage artifact includes Mermaid contracts.
- Stop when no execution artifact or stage loop guidance is needed.

## Review Checks

- Artifact matches the active workspace plan stage.
- Calibration decisions feed the stage loop instead of ad hoc plan files.
