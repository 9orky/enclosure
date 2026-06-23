from __future__ import annotations

from . import domain

apply_limit = domain.apply_limit
validate_report_limit = domain.validate_report_limit

__all__ = [
    "apply_limit",
    "validate_report_limit",
]
