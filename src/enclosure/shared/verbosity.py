from __future__ import annotations

from enum import StrEnum


class ReportVerbosity(StrEnum):
    SUMMARY = "summary"
    STANDARD = "standard"
    DETAILED = "detailed"


def report_verbosity_from_flags(
    *,
    v: bool,
    vv: bool,
    vvv: bool,
) -> ReportVerbosity:
    selected = tuple(flag for flag in (v, vv, vvv) if flag)
    if len(selected) > 1:
        raise ValueError("Choose only one verbosity flag: --v, --vv, or --vvv")
    if v:
        return ReportVerbosity.SUMMARY
    if vv:
        return ReportVerbosity.STANDARD
    if vvv:
        return ReportVerbosity.DETAILED
    return ReportVerbosity.STANDARD


__all__ = [
    "ReportVerbosity",
    "report_verbosity_from_flags",
]
