---
doc_class: rule
rule_kind: planning
audience: agent
purpose: Define the required completeness standard for Mermaid TreeView diagrams used as file contracts.
applies_when:
  - Creating a Mermaid TreeView diagram.
  - Updating a Mermaid TreeView diagram used as a file or package contract.
tags:
  - planning
  - mermaid
  - treeview
read_strategy: full
read_directly: true
---

# Tree Diagrams

## Source Of Truth

- Mermaid TreeView syntax is defined by:
  https://mermaid.ai/open-source/syntax/treeView.html
- Use that page as the SSOT for Mermaid syntax, including `treeView-beta`,
  indentation, labels, and configuration.
- If there is any doubt about which element to use or how to write it, check
  the Mermaid syntax page before editing the diagram.

## Complete Diagram Standard

A complete tree diagram must show the expected file contract precisely enough
that a reader can tell which packages, folders, and files belong to the planned
implementation.

Required elements:

- A single root folder that matches the ownership boundary of the contract.
- `treeView-beta` as the diagram declaration.
- Quoted folder and file labels.
- Indentation as the only parent-child mechanism.
- Every expected package, layer folder, subfolder, and file owned by the
  contract.
- `__init__.py` files when the planned Python package needs them.
- File placement that matches the class and flow diagrams.
- Stable ordering inside a folder: package marker first, then domain,
  application, infrastructure, ui, and support files in a consistent local order.
- No caches, generated runtime artifacts, editor files, or files owned by other
  contracts unless the diagram intentionally defines them.

## Review Checks

- The tree has exactly one contract root.
- Each child is indented under the correct parent.
- Every file referenced by the matching UML or flow diagram appears in the tree.
- Every file in the tree has a clear contract reason.
- Ambiguous syntax has been checked against the SSOT before finalizing.
