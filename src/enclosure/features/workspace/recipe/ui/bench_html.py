from __future__ import annotations

import html

from .. import domain
from ..application import bench


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


def _role_recurrence_bars(
    title: str,
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    module_count: int,
) -> str:
    if not recurrence:
        return f"<p class=\"empty\">No {_escape(title.lower())} recurrence.</p>"
    total = max(module_count, 1)
    return f"<h4>{_escape(title)}</h4><div class=\"role-bars\">" + "".join(
        f"<div class=\"bar-row { _escape(_row_class(_classification_severity(item.label))) }\">"
        f"<code>{_escape(item.path)}</code>"
        "<div class=\"bar-track\">"
        f"<span class=\"{_escape(_bar_class(_classification_severity(item.label)))}\" style=\"width: {int((item.count / total) * 100)}%\"></span>"
        "</div>"
        f"<strong>{item.count}/{total} {_badge(item.label, _classification_severity(item.label))}</strong>"
        "</div>"
        for item in recurrence
    ) + "</div>"


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


def _tree(paths: tuple[str, ...]) -> str:
    if not paths:
        return "<p class=\"empty\">No files.</p>"
    return "<ul class=\"tree\">" + "".join(
        f"<li><code>{_escape(path)}</code></li>"
        for path in paths
    ) + "</ul>"


def _file_content_details(
    files: tuple[domain.RecipeBenchFileContent, ...],
) -> str:
    if not files:
        return ""
    return "<div class=\"contents\">" + "".join(
        "<details>"
        f"<summary>{_escape(file.path)}"
        f"{' (truncated)' if file.truncated else ''}</summary>"
        f"<pre>{_escape(file.content)}</pre>"
        "</details>"
        for file in files
    ) + "</div>"


def _content_weight_list(
    weights: tuple[domain.RecipeBenchContentWeight, ...],
) -> str:
    if not weights:
        return "<p class=\"empty\">No content outliers.</p>"
    return "<ul class=\"tree\">" + "".join(
        "<li>"
        f"<code>{_escape(weight.path)}</code> "
        f"{weight.line_count} lines, {weight.symbol_count} symbols"
        f" - {_escape(weight.reason)}"
        "</li>"
        for weight in weights
    ) + "</ul>"


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


def _interpretation_section() -> str:
    return (
        "<section><h2>Interpretation</h2>"
        "<ul>"
        "<li>Unique residue is local warp stink.</li>"
        "<li>Allowed package internals still count as slot-growth pressure.</li>"
        "<li>Large or symbol-heavy files count as content-weight pressure.</li>"
        "<li>Repeated residue is undeclared pattern pressure.</li>"
        "<li>Very common residue suggests the recipe may be stale.</li>"
        "<li>Many unrelated residues suggest the role may be too broad.</li>"
        "</ul>"
        "</section>"
    )


def _classification_severity(classification: str) -> str:
    return {
        "clean": "clean",
        "local": "low",
        "emerging": "medium",
        "established": "high",
        "unstable": "critical",
    }.get(classification, "")


def _count_severity(count: int) -> str:
    return "high" if count else "clean"


def _summary_class(severity: str) -> str:
    return f"severity-card severity-{severity}" if severity else "severity-card"


def _row_class(severity: str) -> str:
    return f"severity-row severity-{severity}" if severity else "severity-row"


def _bar_class(severity: str) -> str:
    return f"severity-bar severity-{severity}" if severity else "severity-bar"


def _badge(value: str, severity: str) -> str:
    return (
        f"<span class=\"badge severity-{_escape(severity)}\">"
        f"{_escape(value)}</span>"
    )


def _count_cell(count: int) -> str:
    return (
        f"<td class=\"count severity-{_escape(_count_severity(count))}\">"
        f"{count}</td>"
    )


def _bench_css() -> str:
    return """
body {
  margin: 0;
  color: #1f2933;
  background: #f6f8fa;
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
main { max-width: 1180px; margin: 0 auto; padding: 32px; }
header, section {
  background: #ffffff;
  border: 1px solid #d8dee4;
  border-radius: 8px;
  margin-bottom: 18px;
  padding: 20px;
}
.eyebrow { color: #57606a; font-size: 12px; margin: 0 0 4px; text-transform: uppercase; }
h1, h2, h3 { margin: 0 0 14px; line-height: 1.2; }
h1 { font-size: 28px; }
h2 { font-size: 18px; }
h3 { font-size: 15px; }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; padding: 0; border: 0; margin: 16px 0 0; }
.summary div { background: #f6f8fa; border: 1px solid #d8dee4; border-radius: 6px; padding: 12px; }
.summary span { display: block; color: #57606a; font-size: 12px; }
.summary strong { display: block; font-size: 18px; margin-top: 4px; }
.severity-card.severity-clean { background: #eefaf0; border-color: #9be9a8; }
.severity-card.severity-low { background: #fff8c5; border-color: #eac54f; }
.severity-card.severity-medium { background: #fff1e5; border-color: #f69d50; }
.severity-card.severity-high { background: #ffebe9; border-color: #ff8182; }
.severity-card.severity-critical { background: #fbefff; border-color: #bf87ff; }
.columns { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
article { border: 1px solid #d8dee4; border-radius: 6px; padding: 14px; min-width: 0; }
.role-block { margin-top: 14px; }
.tree { list-style: none; margin: 0; padding: 0; }
.tree li { border-bottom: 1px solid #eef1f4; padding: 5px 0; overflow-wrap: anywhere; }
.empty { color: #57606a; }
.contents { margin-top: 16px; }
details { border-top: 1px solid #d8dee4; padding: 8px 0; }
summary { cursor: pointer; font-weight: 600; overflow-wrap: anywhere; }
pre { background: #0f1720; border-radius: 6px; color: #e6edf3; overflow: auto; padding: 12px; white-space: pre-wrap; }
code { font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; min-width: 100%; }
th, td { border: 1px solid #d8dee4; padding: 8px; text-align: left; vertical-align: top; }
thead th { background: #f6f8fa; }
tr.selected th, tr.selected td { background: #fff8c5; }
tr.severity-clean th, tr.severity-clean td { background: #fbfffc; }
tr.severity-low th, tr.severity-low td { background: #fffdf0; }
tr.severity-medium th, tr.severity-medium td { background: #fff8f2; }
tr.severity-high th, tr.severity-high td { background: #fff5f4; }
tr.severity-critical th, tr.severity-critical td { background: #fcf5ff; }
td.count { font-weight: 700; text-align: right; }
td.count.severity-clean { color: #1a7f37; }
td.count.severity-high { color: #cf222e; }
td.hit { background: #dafbe1; color: #116329; font-weight: 700; text-align: center; }
.badge { border-radius: 999px; display: inline-block; font-size: 12px; font-weight: 700; padding: 2px 8px; }
.badge.severity-clean { background: #dafbe1; color: #116329; }
.badge.severity-low { background: #fff8c5; color: #7d4e00; }
.badge.severity-medium { background: #ffdfb6; color: #953800; }
.badge.severity-high { background: #ffebe9; color: #cf222e; }
.badge.severity-critical { background: #fbefff; color: #8250df; }
.bar-row { display: grid; grid-template-columns: minmax(180px, 1fr) minmax(140px, 3fr) 130px; gap: 12px; align-items: center; margin: 10px 0; }
.bar-track { background: #eef1f4; border-radius: 999px; height: 12px; overflow: hidden; }
.bar-track span { display: block; height: 100%; }
.severity-bar.severity-clean { background: #2da44e; }
.severity-bar.severity-low { background: #d4a72c; }
.severity-bar.severity-medium { background: #fb8f44; }
.severity-bar.severity-high { background: #cf222e; }
.severity-bar.severity-critical { background: #8250df; }
@media (max-width: 820px) {
  main { padding: 16px; }
  .columns { grid-template-columns: 1fr; }
  .bar-row { grid-template-columns: 1fr; }
}
""".strip()


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)




__all__ = ["render_bench_all_html", "render_bench_html"]
