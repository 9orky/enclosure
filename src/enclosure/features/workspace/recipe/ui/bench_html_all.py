from __future__ import annotations

from .. import domain
from ..application import bench
from . import bench_html_common

_badge = bench_html_common.badge
_bench_css = bench_html_common.bench_css
_classification_severity = bench_html_common.classification_severity
_count_cell = bench_html_common.count_cell
_count_severity = bench_html_common.count_severity
_escape = bench_html_common.escape
_interpretation_section = bench_html_common.interpretation_section
_role_recurrence_bars = bench_html_common.role_recurrence_bars
_row_class = bench_html_common.row_class
_summary_class = bench_html_common.summary_class


def render_bench_all_html(report: domain.RecipeBenchAllReport) -> str:
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Workspace Warp Index</title>",
            f"<style>{_bench_css()}</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<p class=\"eyebrow\">Workspace Warp Index</p>",
            "<h1>All Mapped Modules</h1>",
            _bench_all_summary_grid(report),
            "</header>",
            _bench_all_violations_section(report),
            _bench_all_worst_modules_section(report),
            _bench_all_roles_section(report),
            _interpretation_section(),
            "</main>",
            "</body>",
            "</html>",
        )
    )


def _bench_all_summary_grid(report: domain.RecipeBenchAllReport) -> str:
    cells = (
        ("Modules", str(report.module_count), ""),
        ("Roles", str(report.role_count), ""),
        ("Modules with warp", str(report.reports_with_warp_count), _count_severity(report.reports_with_warp_count)),
        ("Forbidden residue", str(report.local_residue_count), _count_severity(report.local_residue_count)),
        ("Slot growth", str(report.local_slot_growth_count), _count_severity(report.local_slot_growth_count)),
        ("Content weight", str(report.local_content_weight_count), _count_severity(report.local_content_weight_count)),
        ("Classification", report.classification, _classification_severity(report.classification)),
    )
    return "<section class=\"summary\">" + "".join(
        f"<div class=\"{_escape(_summary_class(severity))}\">"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
        for label, value, severity in cells
    ) + "</section>"


def _bench_all_violations_section(report: domain.RecipeBenchAllReport) -> str:
    if not report.violations:
        return ""
    items = "".join(
        "<li>"
        f"<code>{_escape(violation.code)}</code> "
        f"{_escape(violation.message)}"
        "</li>"
        for violation in report.violations
    )
    return f"<section><h2>Blocking Findings</h2><ul>{items}</ul></section>"


def _bench_all_worst_modules_section(report: domain.RecipeBenchAllReport) -> str:
    ranked_reports = tuple(
        sorted(
            report.reports,
            key=lambda item: (
                -item.local_warp_count,
                -item.repeated_warp_count,
                item.selected_module,
            ),
        )
    )
    if not ranked_reports:
        return "<section><h2>Module Index</h2><p>No mapped modules.</p></section>"
    rows = "".join(_bench_all_module_row(item) for item in ranked_reports)
    return (
        "<section><h2>Module Index</h2>"
        "<div class=\"table-wrap\"><table>"
        "<thead><tr>"
        "<th>Module</th><th>Role</th><th>Expected</th><th>Actual</th>"
        "<th>Warp</th><th>Residue</th><th>Slot Growth</th><th>Content</th>"
        "<th>Repeated</th><th>Classification</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
        "</section>"
    )


def _bench_all_module_row(report: domain.RecipeBenchReport) -> str:
    selected = report.selected
    expected_count = len(selected.expected_files) if selected.module_name else 0
    actual_count = len(selected.actual_files) if selected.module_name else 0
    severity = _classification_severity(report.classification)
    return (
        f"<tr class=\"{_escape(_row_class(severity))}\">"
        f"<th><code>{_escape(report.selected_module)}</code></th>"
        f"<td>{_escape(report.role_name or 'unknown')}</td>"
        f"<td>{expected_count}</td>"
        f"<td>{actual_count}</td>"
        f"{_count_cell(report.local_warp_count)}"
        f"{_count_cell(report.local_residue_count)}"
        f"{_count_cell(report.local_slot_growth_count)}"
        f"{_count_cell(report.local_content_weight_count)}"
        f"{_count_cell(report.repeated_warp_count)}"
        f"<td>{_badge(report.classification, severity)}</td>"
        "</tr>"
    )


def _bench_all_roles_section(report: domain.RecipeBenchAllReport) -> str:
    role_sections = "".join(
        _bench_all_role_section(role_name, role_reports)
        for role_name, role_reports in bench.reports_by_role(report.reports).items()
    )
    if not role_sections:
        role_sections = "<p>No roles to compare.</p>"
    return f"<section><h2>Roles</h2>{role_sections}</section>"


def _bench_all_role_section(
    role_name: str,
    reports: tuple[domain.RecipeBenchReport, ...],
) -> str:
    residue_total = sum(item.local_residue_count for item in reports)
    slot_growth_total = sum(item.local_slot_growth_count for item in reports)
    content_weight_total = sum(item.local_content_weight_count for item in reports)
    repeated_total = sum(item.repeated_warp_count for item in reports)
    recurrence = reports[0].recurrence if reports else ()
    slot_growth_recurrence = reports[0].slot_growth_recurrence if reports else ()
    content_weight_recurrence = reports[0].content_weight_recurrence if reports else ()
    return (
        "<article class=\"role-block\">"
        f"<h3>{_escape(role_name)}</h3>"
        "<p>"
        f"{len(reports)} module(s), {residue_total} residue, "
        f"{slot_growth_total} slot growth, {content_weight_total} content weight, "
        f"{repeated_total} repeated signal(s)."
        "</p>"
        f"{_role_module_table(reports)}"
        f"{_role_recurrence_bars('Forbidden residue', recurrence, len(reports))}"
        f"{_role_recurrence_bars('Slot growth', slot_growth_recurrence, len(reports))}"
        f"{_role_recurrence_bars('Content weight', content_weight_recurrence, len(reports))}"
        "</article>"
    )


def _role_module_table(reports: tuple[domain.RecipeBenchReport, ...]) -> str:
    rows = "".join(
        f"<tr class=\"{_escape(_row_class(_classification_severity(report.classification)))}\">"
        f"<th><code>{_escape(report.selected_module)}</code></th>"
        f"{_count_cell(report.local_warp_count)}"
        f"{_count_cell(report.local_residue_count)}"
        f"{_count_cell(report.local_slot_growth_count)}"
        f"{_count_cell(report.local_content_weight_count)}"
        f"{_count_cell(report.repeated_warp_count)}"
        f"<td>{_badge(report.classification, _classification_severity(report.classification))}</td>"
        "</tr>"
        for report in reports
    )
    return (
        "<div class=\"table-wrap\"><table>"
        "<thead><tr><th>Module</th><th>Warp</th><th>Residue</th>"
        "<th>Slot Growth</th><th>Content</th><th>Repeated</th>"
        "<th>Classification</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )


__all__ = ["render_bench_all_html"]
