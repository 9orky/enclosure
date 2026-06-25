---
doc_class: rule
rule_kind: execution
audience: agent
purpose: Define completeness standards for Mermaid diagrams used as stage contracts.
applies_when:
  - Creating or updating Mermaid diagrams in workspace plan stage artifacts.
  - Creating or updating Mermaid diagrams used as schemas, flows, file trees, or implementation contracts.
tags:
  - execution
  - mermaid
  - contract-diagrams
read_strategy: full
read_directly: true
---

# Contract Diagrams

## Source Of Truth

- Flowchart syntax: https://mermaid.ai/open-source/syntax/flowchart.html
- Class diagram syntax: https://mermaid.ai/open-source/syntax/classDiagram.html#return-type
- TreeView syntax: https://mermaid.ai/open-source/syntax/treeView.html
- Check the relevant Mermaid page before finalizing ambiguous syntax.

## Flowcharts

- Declare a flow direction that matches the reading order.
- Use stable lowercase node ids and rendered labels that state the role:
  command, signal, usecase, service, interface, port, adapter, domain, model,
  decision, store, document, output, or halt.
- Group swimlanes by role with subgraphs when ownership or flow would otherwise
  be unclear.
- Label non-obvious edges and every outgoing decision branch.
- Show terminal output, halt, or blocked nodes for important branches.

## Class Diagrams

- Show every class-like symbol that is part of the contract: class, interface,
  abstract class, and parent class.
- Include visible ownership metadata when file or role ownership matters.
- Give properties explicit types and methods explicit return types.
- Show inheritance, realization, association, aggregation, composition, and
  dependency relations that are part of the design.
- Label relations when dependency or role is not self-evident.

## Tree Diagrams

- Use `treeView-beta` with one quoted root folder matching the ownership boundary.
- Include every expected package, layer folder, subfolder, and file owned by the
  contract.
- Include `__init__.py` when the Python package needs it.
- Keep ordering stable: package marker first, then domain, application,
  infrastructure, ui, and support files in a consistent local order.
- Exclude caches, generated runtime artifacts, editor files, and files owned by
  other contracts.

## Review Checks

- Every implementation node names its owner when ownership matters.
- Every port/adapter implementation relation is visible.
- Every file referenced by a flow or class diagram appears in the tree diagram.
- No diagram relies on ambiguous Mermaid shorthand.
