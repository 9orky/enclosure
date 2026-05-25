from __future__ import annotations

from modwire.architecture import ArchitecturePolicyEvaluator

from enclosure.shared import architecture_code

from . import domain


def build_boundaries_report() -> domain.BoundariesReport:
    code_analysis = architecture_code.extract_architecture_code()
    return domain.BoundariesReport(
        **code_analysis.report_fields(),
        violations=tuple(
            ArchitecturePolicyEvaluator().evaluate(
                architecture_code.tracked_dependency_graph(code_analysis.code_map),
                code_analysis.matching_config,
            )
        ),
    )
