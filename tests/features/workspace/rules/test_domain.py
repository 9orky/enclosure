from __future__ import annotations

import unittest
from pathlib import Path

from enclosure.features.workspace.rules import domain


class WorkspaceRulesTest(unittest.TestCase):
    def test_local_policy_uses_local_body_contract(self) -> None:
        policy = domain.RuleSchemaPolicy.default()
        document_file = domain.RuleDocumentFile(
            path=Path("local/structure/MODULE.md"),
            content="""---
doc_class: policy
rule_kind: policy
scope: local
generated_by: agent
validation_version: 1
profile_kind: module_seams
discovered_from:
  - ../../../src/enclosure/
narrows_paths:
  - ../../shared/structure/MODULE.md
audience: agent
purpose: Record the local package seam.
applies_when:
  - Shared module guidance is already in scope.
tags:
  - local
read_directly: false
tightens_paths:
  - ../../shared/structure/MODULE.md
escalation_paths: []
---

# Local Module

## Rules

- Package root is the public seam.

## Checks

- Public imports are intentional.
""",
        )

        check = policy.inspect_document(document_file)

        self.assertEqual((), check.violations)
        self.assertEqual(domain.RuleDocumentScope.LOCAL, check.document.scope)

    def test_local_content_threshold_reports_oversized_body(self) -> None:
        policy = domain.RuleSchemaPolicy.from_config(
            domain.RulesConfig(
                local=domain.LocalRulesConfig(max_content_chars=8),
            )
        )
        document_file = domain.RuleDocumentFile(
            path=Path("local/structure/MODULE.md"),
            content="""---
doc_class: policy
rule_kind: policy
scope: local
audience: agent
purpose: Record the local package seam.
applies_when:
  - Shared module guidance is already in scope.
tags:
  - local
read_directly: false
---

# Local Module

## Rules

- Package root is the public seam.

## Checks

- Public imports are intentional.
""",
        )

        violations = policy.validate_file(document_file)

        self.assertEqual(1, len(violations))
        self.assertEqual("local-content-too-large", violations[0].code)

    def test_local_navigation_references_resolve_across_local_and_shared(self) -> None:
        policy = domain.RuleSchemaPolicy.default()
        document_file = domain.RuleDocumentFile(
            path=Path("local/structure/INDEX.md"),
            content="""---
doc_class: navigational
rule_kind: navigation
scope: local
audience: agent
purpose: Route local structure supplements.
applies_when:
  - Shared structure guidance is already in scope.
tags:
  - local
read_directly: false
tightens_paths:
  - ../../shared/structure/INDEX.md
entrypoint: true
read_strategy: progressive
child_paths:
  - MODULE.md
---

# Local Structure

## Use This Branch When

- Local structure facts are needed.

## Stop Or Descend

- Read [MODULE.md](MODULE.md).

## Review Checks

- Stop at the shallowest local supplement.
""",
        )
        check = policy.inspect_document(document_file)

        violations = policy.validate_references(
            document=check.document,
            known_paths={
                Path("local/structure/INDEX.md"),
                Path("local/structure/MODULE.md"),
                Path("shared/structure/INDEX.md"),
            },
        )

        self.assertEqual((), check.violations)
        self.assertEqual((), violations)


if __name__ == "__main__":
    unittest.main()
