---
doc_class: rule
rule_kind: planning
audience: agent
purpose: Define the required completeness standard for Mermaid flowcharts used as planning contracts.
applies_when:
  - Creating a Mermaid flowchart.
  - Updating a Mermaid flowchart used as a schema, flow, or implementation contract.
tags:
  - planning
  - mermaid
  - flowchart
read_strategy: full
read_directly: true
---

# Flow Diagrams

## Source Of Truth

- Mermaid flowchart syntax is defined by:
  https://mermaid.ai/open-source/syntax/flowchart.html
- Use that page as the SSOT for Mermaid syntax, including direction, nodes,
  shapes, edges, labels, subgraphs, classes, and warnings.
- If there is any doubt about which element to use or how to write it, check
  the Mermaid syntax page before editing the diagram.

## Complete Diagram Standard

A complete flow diagram must show the behavioral contract precisely enough that
a reader can follow entry points, decisions, implementation owners, ports,
adapters, data, and outputs without reading source files.

Required elements:

- A declared flow direction that matches the reading order of the contract.
- Stable node ids that are short, lowercase, and meaningful.
- Rendered node labels that include the node kind, such as command, signal,
  usecase, service, interface, port, adapter, domain, model, decision, or output.
- File and class ownership in node labels for implementation-owned nodes.
- Subgraphs that group swimlanes by role, such as commands, signals, use cases,
  application services, domain models, ports, adapters, and outputs.
- Semantically appropriate node shapes when the role matters: rectangles for
  process/service nodes, diamonds for decisions, stadiums for start/end style
  entry points, cylinders for stores, and documents for generated files.
- Explicit edge labels whenever the relation is not obvious from adjacent node
  names.
- Dotted edges for shape, implementation, or dependency relations that are not
  direct runtime flow.
- Terminal, halt, blocked, or output nodes for every important branch.
- Class definitions for each visual category used by nodes.

## Review Checks

- The diagram avoids lowercase `end` as a node label and avoids ambiguous node
  ids that trigger Mermaid edge shorthand.
- Every implementation node names its file and class.
- Every port/adapter implementation relation is visible and labeled.
- Branching decisions have labeled outgoing paths.
- Every meaningful output or halt state is represented.
- Ambiguous syntax has been checked against the SSOT before finalizing.
