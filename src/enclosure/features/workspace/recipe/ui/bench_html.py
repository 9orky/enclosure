from __future__ import annotations

from .. import domain
from . import bench_html_all, bench_html_common

_badge = bench_html_common.badge
_bar_class = bench_html_common.bar_class
_bench_css = bench_html_common.bench_css
_classification_severity = bench_html_common.classification_severity
_content_weight_list = bench_html_common.content_weight_list
_count_cell = bench_html_common.count_cell
_count_severity = bench_html_common.count_severity
_escape = bench_html_common.escape
_file_content_details = bench_html_common.file_content_details
_interpretation_section = bench_html_common.interpretation_section
_role_recurrence_bars = bench_html_common.role_recurrence_bars
_row_class = bench_html_common.row_class
_summary_class = bench_html_common.summary_class
_tree = bench_html_common.tree
render_bench_all_html = bench_html_all.render_bench_all_html


def render_bench_html(report: domain.RecipeBenchReport) -> str:
    selected = report.selected
    residue_paths = tuple(item.path for item in report.recurrence)
    title = f"Bench Preview: {report.selected_module}"
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_escape(title)}</title>",
            f"<style>{_bench_css()}</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<p class=\"eyebrow\">Bench Preview Warp Report</p>",
            f"<h1>{_escape(report.selected_module)}</h1>",
            _summary_grid(report),
            "</header>",
            _violations_section(report),
            _three_column_section(selected),
            _matrix_section(report, residue_paths),
            _recurrence_section(report),
            _interpretation_section(),
            "</main>",
            "</body>",
            "</html>",
        )
    )


def _summary_grid(report: domain.RecipeBenchReport) -> str:
    cells = (
        ("Recipe role", report.role_name or "unknown", ""),
        ("Same-role modules", str(report.same_role_module_count), ""),
        ("Local warp", str(report.local_warp_count), _count_severity(report.local_warp_count)),
        ("Forbidden residue", str(report.local_residue_count), _count_severity(report.local_residue_count)),
        ("Slot growth", str(report.local_slot_growth_count), _count_severity(report.local_slot_growth_count)),
        ("Content weight", str(report.local_content_weight_count), _count_severity(report.local_content_weight_count)),
        ("Repeated warp", str(report.repeated_warp_count), _count_severity(report.repeated_warp_count)),
        ("Classification", report.classification, _classification_severity(report.classification)),
    )
    return "<section class=\"summary\">" + "".join(
        f"<div class=\"{_escape(_summary_class(severity))}\">"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
        for label, value, severity in cells
    ) + "</section>"


def _violations_section(report: domain.RecipeBenchReport) -> str:
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


def _three_column_section(selected: domain.RecipeBenchModule) -> str:
    if not selected.module_name:
        return (
            "<section><h2>Module Bench</h2>"
            "<p>No selected module data could be collected.</p></section>"
        )
    return (
        "<section><h2>Module Bench</h2>"
        "<div class=\"columns\">"
        f"<article><h3>Actual Tree</h3>{_tree(selected.actual_files)}"
        f"{_file_content_details(selected.file_contents)}</article>"
        f"<article><h3>Recipe Expected</h3>{_tree(selected.expected_files)}</article>"
        f"<article><h3>Missing Expected</h3>{_tree(selected.missing_files)}"
        f"<h3>Forbidden Residue</h3>{_tree(selected.residue_files)}"
        f"<h3>Slot Growth</h3>{_tree(selected.slot_growth_files)}"
        f"<h3>Content Weight</h3>{_content_weight_list(selected.content_weights)}</article>"
        "</div>"
        "</section>"
    )


def _matrix_section(
    report: domain.RecipeBenchReport,
    residue_paths: tuple[str, ...],
) -> str:
    if not report.same_role_modules:
        return "<section><h2>Same-Role Matrix</h2><p>No modules to compare.</p></section>"
    if not residue_paths:
        return (
            "<section><h2>Same-Role Matrix</h2>"
            "<p>No residue paths were found across the same-role modules.</p></section>"
        )

    header_cells = "".join(
        f"<th><code>{_escape(path)}</code></th>"
        for path in residue_paths
    )
    rows = "".join(
        _matrix_row(report, bench_module, residue_paths)
        for bench_module in report.same_role_modules
    )
    return (
        "<section><h2>Same-Role Matrix</h2>"
        "<div class=\"table-wrap\"><table>"
        f"<thead><tr><th>Module</th>{header_cells}</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
        "</section>"
    )


def _matrix_row(
    report: domain.RecipeBenchReport,
    bench_module: domain.RecipeBenchModule,
    residue_paths: tuple[str, ...],
) -> str:
    residue_set = set(bench_module.residue_files)
    selected_class = (
        " class=\"selected\""
        if bench_module.module_name == report.selected_module
        else ""
    )
    cells = "".join(
        "<td class=\"hit\">yes</td>" if path in residue_set else "<td></td>"
        for path in residue_paths
    )
    return (
        f"<tr{selected_class}>"
        f"<th><code>{_escape(bench_module.module_name)}</code></th>"
        f"{cells}</tr>"
    )


def _recurrence_section(report: domain.RecipeBenchReport) -> str:
    return (
        "<section><h2>Recurrence</h2>"
        f"{_role_recurrence_bars('Forbidden residue', report.recurrence, report.same_role_module_count)}"
        f"{_role_recurrence_bars('Slot growth', report.slot_growth_recurrence, report.same_role_module_count)}"
        f"{_role_recurrence_bars('Content weight', report.content_weight_recurrence, report.same_role_module_count)}"
        "</section>"
    )


__all__ = ["render_bench_all_html", "render_bench_html"]
