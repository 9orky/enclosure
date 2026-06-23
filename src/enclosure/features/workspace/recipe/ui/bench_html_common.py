from __future__ import annotations

import html

from .. import domain


def role_recurrence_bars(
    title: str,
    recurrence: tuple[domain.RecipeBenchRecurrence, ...],
    module_count: int,
) -> str:
    if not recurrence:
        return f"<p class=\"empty\">No {escape(title.lower())} recurrence.</p>"
    total = max(module_count, 1)
    return f"<h4>{escape(title)}</h4><div class=\"role-bars\">" + "".join(
        f"<div class=\"bar-row { escape(row_class(classification_severity(item.label))) }\">"
        f"<code>{escape(item.path)}</code>"
        "<div class=\"bar-track\">"
        f"<span class=\"{escape(bar_class(classification_severity(item.label)))}\" style=\"width: {int((item.count / total) * 100)}%\"></span>"
        "</div>"
        f"<strong>{item.count}/{total} {badge(item.label, classification_severity(item.label))}</strong>"
        "</div>"
        for item in recurrence
    ) + "</div>"


def tree(paths: tuple[str, ...]) -> str:
    if not paths:
        return "<p class=\"empty\">No files.</p>"
    return "<ul class=\"tree\">" + "".join(
        f"<li><code>{escape(path)}</code></li>"
        for path in paths
    ) + "</ul>"


def file_content_details(
    files: tuple[domain.RecipeBenchFileContent, ...],
) -> str:
    if not files:
        return ""
    return "<div class=\"contents\">" + "".join(
        "<details>"
        f"<summary>{escape(file.path)}"
        f"{' (truncated)' if file.truncated else ''}</summary>"
        f"<pre>{escape(file.content)}</pre>"
        "</details>"
        for file in files
    ) + "</div>"


def content_weight_list(
    weights: tuple[domain.RecipeBenchContentWeight, ...],
) -> str:
    if not weights:
        return "<p class=\"empty\">No content outliers.</p>"
    return "<ul class=\"tree\">" + "".join(
        "<li>"
        f"<code>{escape(weight.path)}</code> "
        f"{weight.line_count} lines, {weight.symbol_count} symbols"
        f" - {escape(weight.reason)}"
        "</li>"
        for weight in weights
    ) + "</ul>"


def interpretation_section() -> str:
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


def classification_severity(classification: str) -> str:
    return {
        "clean": "clean",
        "local": "low",
        "emerging": "medium",
        "established": "high",
        "unstable": "critical",
    }.get(classification, "")


def count_severity(count: int) -> str:
    return "high" if count else "clean"


def summary_class(severity: str) -> str:
    return f"severity-card severity-{severity}" if severity else "severity-card"


def row_class(severity: str) -> str:
    return f"severity-row severity-{severity}" if severity else "severity-row"


def bar_class(severity: str) -> str:
    return f"severity-bar severity-{severity}" if severity else "severity-bar"


def badge(value: str, severity: str) -> str:
    return (
        f"<span class=\"badge severity-{escape(severity)}\">"
        f"{escape(value)}</span>"
    )


def count_cell(count: int) -> str:
    return (
        f"<td class=\"count severity-{escape(count_severity(count))}\">"
        f"{count}</td>"
    )


def bench_css() -> str:
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


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


__all__ = [
    "badge",
    "bar_class",
    "bench_css",
    "classification_severity",
    "content_weight_list",
    "count_cell",
    "count_severity",
    "escape",
    "file_content_details",
    "interpretation_section",
    "role_recurrence_bars",
    "row_class",
    "summary_class",
    "tree",
]
