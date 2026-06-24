---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route shared planning artifact guidance.
applies_when:
  - The task creates or updates planning artifacts.
  - The task creates or updates diagrams used as planning contracts.
tags:
  - planning
  - routing
  - diagrams
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - UML_CLASS_DIAGRAMS.md
  - FLOW_DIAGRAMS.md
  - TREE_DIAGRAMS.md
---

# Planning

## Use This Branch When

- A planning artifact needs a diagram, schema, or implementation contract.
- A Mermaid UML class diagram is used to communicate implementation shape.
- A Mermaid flowchart or TreeView diagram is used as a planning contract.

## Stop Or Descend

- Read [UML_CLASS_DIAGRAMS.md](UML_CLASS_DIAGRAMS.md) before creating or
  changing a Mermaid class diagram.
- Read [FLOW_DIAGRAMS.md](FLOW_DIAGRAMS.md) before creating or changing a
  Mermaid flowchart used as a planning contract.
- Read [TREE_DIAGRAMS.md](TREE_DIAGRAMS.md) before creating or changing a
  Mermaid TreeView diagram used as a file contract.
- Stop here when the planning artifact does not include a diagram contract.

## Review Checks

- The matching diagram rule is read before editing diagram contracts.
- The external Mermaid syntax reference is treated as the source of truth.
