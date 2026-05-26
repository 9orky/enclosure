from __future__ import annotations

from pathlib import Path

import pytest

from enclosure.features.workspace.plan import domain


@pytest.mark.parametrize(
    "value",
    (
        "",
        ".",
        "..",
        "../plan",
        "nested/plan",
        "/absolute",
        "Not-A-Slug",
        "not_a_slug",
        "plan.md",
    ),
)
def test_plan_name_rejects_values_outside_single_slug(value: str) -> None:
    with pytest.raises(ValueError):
        domain.PlanName(value)


def test_plan_name_resolves_document_path_under_plans_root() -> None:
    plan_name = domain.PlanName("module-design")

    assert plan_name.document_path(Path(".enclosure/plans")) == Path(
        ".enclosure/plans/module-design.md"
    )


def test_plan_scaffold_includes_required_sections() -> None:
    content = domain.render_plan_scaffold(domain.PlanName("module-design"))

    assert content.startswith("# Module Design\n")
    assert "Status: Draft" in content
    for heading in domain.PLAN_SECTION_HEADINGS:
        assert f"## {heading}" in content
