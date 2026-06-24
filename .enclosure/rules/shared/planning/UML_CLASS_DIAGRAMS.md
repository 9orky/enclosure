---
doc_class: rule
rule_kind: planning
audience: agent
purpose: Define the required completeness standard for Mermaid UML class diagrams used as planning contracts.
applies_when:
  - Creating a Mermaid class diagram.
  - Updating a Mermaid class diagram used as a schema or implementation contract.
tags:
  - planning
  - mermaid
  - uml
  - class-diagram
read_strategy: full
read_directly: true
---

# UML Class Diagrams

## Source Of Truth

- Mermaid class diagram syntax is defined by:
  https://mermaid.ai/open-source/syntax/classDiagram.html#return-type
- Use that page as the SSOT for Mermaid syntax, including return types,
  generics, relation labels, cardinality, annotations, and visibility markers.
- If there is any doubt about which element to use or how to write it, check
  the Mermaid syntax page before editing the diagram.

## Complete Diagram Standard

A complete class diagram must show the implementation contract precisely enough
that a reader can tell what belongs where without reading source files.

Required elements:

- Classes, interfaces, abstract classes, and parent classes that are part of the
  contract.
- Class ownership metadata in a rendered-visible form, such as one stereotype
  row that combines role and file path when both are needed.
- Properties with explicit types.
- Methods for all relevant visibilities with explicit return types, including
  public, private, protected, and package/internal members when they are part of
  the contract.
- Generic types where they are the correct type shape, such as list, mapping, or
  optional-like values.
- A meaningful non-generic return type when one exists; use generic or empty
  return shapes only when no more specific type is proper.
- Inheritance, realization, association, aggregation, composition, dependency,
  and other relations that match the intended design.
- Relation labels that explain the dependency or role when the relation is not
  self-evident.
- Cardinality on relations whenever the number of related objects matters.

## Review Checks

- Every class-like symbol has the right kind: class, interface, abstract class,
  or parent class.
- Every property and method shown in the contract has a type or return type.
- Every implementation relation points at the interface or abstract contract it
  implements.
- Every relation uses Mermaid syntax from the SSOT page.
- Ambiguous syntax has been checked against the SSOT before finalizing.
