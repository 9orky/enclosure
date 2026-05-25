from __future__ import annotations

from enclosure.shared import architecture_code

from . import domain


def build_shape_report() -> domain.ShapeReport:
    code_analysis = architecture_code.extract_architecture_code()
    return domain.ShapeReport(
        **code_analysis.report_fields(),
        violations=domain.evaluate_shape(code_analysis.code_map, code_analysis.config),
    )


__all__ = ["build_shape_report"]
