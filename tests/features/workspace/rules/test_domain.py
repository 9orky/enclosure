from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from enclosure.features.workspace.rules.domain import documents, graph, inference, policy


class WorkspaceRulesTest(unittest.TestCase):
    def test_local_policy_uses_local_body_contract(self) -> None:
        rule_schema_policy = policy.RuleSchemaPolicy.default()
        document_file = documents.RuleDocumentFile(
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

        check = rule_schema_policy.inspect_document(document_file)

        self.assertEqual((), check.violations)
        self.assertEqual(documents.RuleDocumentScope.LOCAL, check.document.scope)

    def test_local_content_threshold_reports_oversized_body(self) -> None:
        rule_schema_policy = policy.RuleSchemaPolicy.from_config(
            SimpleNamespace(local=SimpleNamespace(max_content_chars=8))
        )
        document_file = documents.RuleDocumentFile(
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

        violations = rule_schema_policy.validate_file(document_file)

        self.assertEqual(1, len(violations))
        self.assertEqual("local-content-too-large", violations[0].code)

    def test_local_navigation_references_resolve_across_local_and_shared(self) -> None:
        rule_schema_policy = policy.RuleSchemaPolicy.default()
        document_file = documents.RuleDocumentFile(
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
        check = rule_schema_policy.inspect_document(document_file)

        violations = rule_schema_policy.validate_references(
            document=check.document,
            known_paths={
                Path("local/structure/INDEX.md"),
                Path("local/structure/MODULE.md"),
                Path("shared/structure/INDEX.md"),
            },
        )

        self.assertEqual((), check.violations)
        self.assertEqual((), violations)

    def test_rule_route_uses_shared_branch_and_local_tightening(self) -> None:
        documents = (
            _document(
                Path("INDEX.md"),
                _navigation_content(
                    tags=("rules",),
                    read_directly=True,
                    child_paths=("shared/INDEX.md",),
                ),
            ),
            _document(
                Path("shared/INDEX.md"),
                _navigation_content(
                    tags=("shared",),
                    read_directly=True,
                    child_paths=("structure/INDEX.md",),
                ),
            ),
            _document(
                Path("shared/structure/INDEX.md"),
                _navigation_content(
                    tags=("structure",),
                    child_paths=("MODULE.md",),
                ),
            ),
            _document(
                Path("local/structure/INDEX.md"),
                _navigation_content(
                    scope="local",
                    tags=("local", "structure"),
                    tightens_paths=("../../shared/structure/INDEX.md",),
                    child_paths=("MODULE.md",),
                ),
            ),
        )

        plan = graph.build_rule_read_plan(documents, ("structure",))

        self.assertEqual(
            (
                Path("INDEX.md"),
                Path("shared/INDEX.md"),
                Path("shared/structure/INDEX.md"),
                Path("local/structure/INDEX.md"),
            ),
            tuple(step.path for step in plan.steps),
        )
        self.assertEqual("local/structure/INDEX.md", plan.stop_point)
        self.assertTrue(plan.steps[-1].local_supplement)

    def test_rule_route_reports_unknown_tags_with_available_tags(self) -> None:
        plan = graph.build_rule_read_plan(
            (
                _document(
                    Path("shared/structure/INDEX.md"),
                    _navigation_content(
                        tags=("structure",),
                        child_paths=("MODULE.md",),
                    ),
                ),
            ),
            ("missing",),
        )

        self.assertFalse(plan.found)
        self.assertEqual(("structure",), plan.available_tags)

    def test_path_inference_selects_structure_without_language_tags(self) -> None:
        selections = inference.infer_rule_tag_selections(
            path_facts=(
                inference.RulePathFacts(
                    relative_path="src/enclosure/features/workspace/rules/domain.py",
                    is_architecture_path=True,
                    is_configured_source_file=True,
                ),
            ),
            task="",
        )

        self.assertEqual(
            ("structure",),
            inference.selected_tags(selections),
        )

    def test_path_inference_selects_configured_module_and_layers(self) -> None:
        selections = inference.infer_rule_tag_selections(
            path_facts=(
                inference.RulePathFacts(
                    relative_path="src/features/orders/application/main.ts",
                    is_architecture_path=True,
                    is_configured_source_file=True,
                    matches_module=True,
                    matches_layer=True,
                ),
            ),
            task="",
        )

        self.assertEqual(
            ("structure", "module", "layers"),
            inference.selected_tags(selections),
        )

    def test_task_inference_selects_refactoring_tags(self) -> None:
        selections = inference.infer_rule_tag_selections(
            path_facts=(),
            task="refactoring",
        )

        self.assertEqual(
            ("change", "refactoring"),
            inference.selected_tags(selections),
        )

    def test_task_inference_selects_calibration_tags(self) -> None:
        selections = inference.infer_rule_tag_selections(
            path_facts=(),
            task="calibration",
        )

        self.assertEqual(
            ("execution", "calibration"),
            inference.selected_tags(selections),
        )

    def test_task_inference_selects_module_start_tag(self) -> None:
        selections = inference.infer_rule_tag_selections(
            path_facts=(),
            task="start coding module",
        )

        self.assertEqual(("module-start",), inference.selected_tags(selections))

    def test_rule_graph_reports_invalid_direct_read_and_unreachable_doc(self) -> None:
        documents = (
            _document(
                Path("shared/direct.md"),
                _policy_content(tags=("direct",), read_directly=True),
            ),
            _document(
                Path("shared/structure/MODULE.md"),
                _policy_content(tags=("module",)),
            ),
        )

        codes = {
            finding.violation.code
            for finding in graph.validate_rule_graph(documents)
        }

        self.assertIn("invalid-direct-read", codes)
        self.assertIn("unreachable-rule-document", codes)

    def test_rule_graph_reports_local_rule_without_shared_anchor(self) -> None:
        document = _document(
            Path("local/structure/MODULE.md"),
            _policy_content(scope="local", tags=("local", "module")),
        )

        codes = {
            finding.violation.code
            for finding in graph.validate_rule_graph((document,))
        }

        self.assertIn("local-rule-without-shared-anchor", codes)

    def test_rule_graph_reports_unsupported_and_unusable_navigation(self) -> None:
        document = _document(
            Path("shared/structure/INDEX.md"),
            _navigation_content(
                tags=("structure",),
                read_strategy="wide",
                child_paths=("MISSING.md",),
            ),
        )

        codes = {
            finding.violation.code
            for finding in graph.validate_rule_graph((document,))
        }

        self.assertIn("unsupported-read-strategy", codes)
        self.assertIn("unusable-navigation-route", codes)

def _document(path: Path, content: str) -> documents.RuleDocument:
    return documents.RuleDocument.from_file(
        documents.RuleDocumentFile(
            path=path,
            content=content,
        )
    )


def _navigation_content(
    *,
    tags: tuple[str, ...],
    scope: str = "shared",
    read_directly: bool = False,
    read_strategy: str = "progressive",
    child_paths: tuple[str, ...],
    tightens_paths: tuple[str, ...] = (),
) -> str:
    return f"""---
doc_class: navigational
rule_kind: navigation
scope: {scope}
audience: agent
purpose: Route test guidance.
applies_when:
  - Test guidance is needed.
tags:
{_yaml_items(tags)}read_directly: {_yaml_bool(read_directly)}
tightens_paths:
{_yaml_items(tightens_paths)}entrypoint: true
read_strategy: {read_strategy}
child_paths:
{_yaml_items(child_paths)}---

# Test Navigation

## Stop Or Descend

- Read the child.

## Review Checks

- Route is deterministic.
"""


def _policy_content(
    *,
    tags: tuple[str, ...],
    scope: str = "shared",
    read_directly: bool = False,
) -> str:
    return f"""---
doc_class: policy
rule_kind: policy
scope: {scope}
audience: agent
purpose: Test policy.
applies_when:
  - Policy is needed.
tags:
{_yaml_items(tags)}read_directly: {_yaml_bool(read_directly)}
---

# Test Policy

## Required Decisions

- Decision.

## Core Rules

- Rule.

## Review Checks

- Check.
"""


def _yaml_items(values: tuple[str, ...]) -> str:
    if not values:
        return "  []\n"
    return "".join(f"  - {value}\n" for value in values)


def _yaml_bool(value: bool) -> str:
    return "true" if value else "false"


if __name__ == "__main__":
    unittest.main()
