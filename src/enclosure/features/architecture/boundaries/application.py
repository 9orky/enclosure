from __future__ import annotations

from enclosure.features.architecture import flow
from enclosure.shared import architecture_code

from . import domain


def build_boundaries_report() -> domain.BoundariesReport:
    code_analysis = architecture_code.extract_architecture_code()
    return domain.BoundariesReport(
        **code_analysis.report_fields(),
        violations=flow.evaluate_policy(
            code_analysis.code_map.tracked_only().graph,
            code_analysis.matching_config,
        ),
    )
