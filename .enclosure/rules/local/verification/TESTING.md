---
doc_class: policy
rule_kind: policy
scope: local
audience: agent
purpose: Require repository tests to prove behavior only through CLI commands.
applies_when:
  - Tests are created, changed, reviewed, or run.
  - A verification seam is selected for this repository.
tags:
  - local
  - verification
  - testing
  - cli
read_directly: false
tightens_paths:
  - ../../shared/verification/TESTING.md
---

# Local Testing

## Rules

- Tests in this repository are functional tests only.
- Tests must execute CLI commands and assert command results, output, generated files, errors, or violations.
- Tests must not import from `src/` or from `enclosure.features`.
- Tests must not call feature, application, domain, infrastructure, or UI functions directly.
- Test fixtures may create or copy probe projects, run commands inside them, and inspect filesystem results.
- Production code must not add test-only public seams to support tests.

## Checks

- Every test reaches behavior through a CLI command.
- No test imports from `src/` or `enclosure.features`.
- Assertions describe observable command behavior or probe-project state.
