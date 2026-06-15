---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define recipe module ladder checks as mechanical file and package shape contracts.
applies_when:
  - A recipe describes how a module shape grows from files into packages.
  - Drift checking must distinguish required seams from allowed private internals.
tags:
  - structure
  - recipes
  - module-ladder
read_directly: false
escalation_paths:
  - ../architecture/BOUNDARIES.md
---

# Module Ladder

## Required Decisions

- Slot names and whether each slot is a file, package, or split slot.
- Required seams for package slots.
- Included fragments and their composition order.
- Drift findings that should block the current recipe shape.

## Core Rules

- A module ladder is a recipe shape contract, not an architecture style.
- Recipes describe slots, required files, forbidden file/package combinations,
  and package seams.
- Reuse fixed `fragment` recipes with `includes`; do not create a new archetype
  for every combination of slots.
- Slot names have no global meaning; a project may call slots `domain`,
  `handlers`, `controllers`, `jobs`, or anything else.
- Package slots require a package seam and may own private internal files.
- Drift checks report missing required seams and forbidden shapes; they do not
  report private files under an allowed package slot.

## Review Checks

- Required files exist.
- Included fragments resolve without cycles.
- File slots do not also have package folders.
- Package slots do not also have sibling files.
- Split slots declare their child files or packages explicitly.
