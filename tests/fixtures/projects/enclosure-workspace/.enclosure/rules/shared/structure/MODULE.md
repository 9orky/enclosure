---
doc_class: policy
rule_kind: policy
scope: shared
audience: agent
purpose: Keep package seams explicit.
applies_when:
  - Module structure is changing.
tags:
  - shared
read_directly: false
---

# Shared Module

## Required Decisions

- Public seam.

## Core Rules

- Keep package boundaries intentional.

## Review Checks

- Imports follow the public seam.
