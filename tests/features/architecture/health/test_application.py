from __future__ import annotations

from enclosure.features.architecture.health import application


def test_findings_use_internal_candidate_unresolved_calls_for_attention() -> None:
    findings = application._findings(
        files_checked=1,
        boundary_violation_count=0,
        shape_violation_count=0,
        unknown_file_count=0,
        pressure_clusters=(),
        unresolved_internal_call_count=2,
        unresolved_non_actionable_call_count=5,
        coherence_finding_count=0,
    )

    assert len(findings) == 1
    assert findings[0].subject == "unresolved internal call candidates"
    assert "2 internal candidate" in findings[0].detail
    assert "5 builtin, external, or dynamic" in findings[0].detail


def test_findings_ignore_context_only_unresolved_calls() -> None:
    findings = application._findings(
        files_checked=1,
        boundary_violation_count=0,
        shape_violation_count=0,
        unknown_file_count=0,
        pressure_clusters=(),
        unresolved_internal_call_count=0,
        unresolved_non_actionable_call_count=5,
        coherence_finding_count=0,
    )

    assert findings == ()


def test_unknown_file_finding_mentions_module_tags_or_realms() -> None:
    findings = application._findings(
        files_checked=1,
        boundary_violation_count=0,
        shape_violation_count=0,
        unknown_file_count=2,
        pressure_clusters=(),
        unresolved_internal_call_count=0,
        unresolved_non_actionable_call_count=0,
        coherence_finding_count=0,
    )

    assert len(findings) == 1
    assert findings[0].detail == (
        "2 file(s) outside configured module tags or realms."
    )
