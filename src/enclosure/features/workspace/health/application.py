from __future__ import annotations

import enclosure.features.workspace.config
import enclosure.features.workspace.recipe
import enclosure.features.workspace.rules
from enclosure.shared import layout

from . import domain


def build_workspace_health_report() -> domain.WorkspaceHealthReport:
    project_root = layout.current_project_root()
    project_layout = layout.current_layout()
    target_dir = project_layout.target_dir(project_root)
    rules_dir = project_layout.rules_dir(project_root)
    local_rules_dir = project_layout.local_rules_dir(project_root)
    shared_rules_dir = rules_dir / "shared"
    recipes_dir = layout.current_recipes_root()

    findings: list[domain.WorkspaceHealthFinding] = []
    config_path = project_layout.config_path(project_root, None)
    config_present = False

    try:
        _project_root, config_path, _workspace_settings = (
            enclosure.features.workspace.config.load_config()
        )
        config_present = config_path.is_file()
    except Exception as exc:
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="error",
                category="config",
                subject="workspace config",
                detail=str(exc),
            )
        )

    rules_report = None
    try:
        rules_report = enclosure.features.workspace.rules.build_rule_schema_report()
    except Exception as exc:
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="error",
                category="rules",
                subject="workspace rules",
                detail=str(exc),
            )
        )

    recipe_report = None
    try:
        recipe_report = enclosure.features.workspace.recipe.check_recipes(
            recipe_root=recipes_dir,
            recipe_name=None,
            target_path=None,
            variables={},
        )
    except Exception as exc:
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="error",
                category="recipe",
                subject="workspace recipes",
                detail=str(exc),
            )
        )

    findings.extend(
        _filesystem_findings(
            target_dir_present=target_dir.is_dir(),
            rules_dir_present=rules_dir.is_dir(),
            local_rules_dir_present=local_rules_dir.is_dir(),
            shared_rules_dir_present=shared_rules_dir.is_dir(),
        )
    )
    if rules_report is not None and rules_report.has_findings:
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="error",
                category="rules",
                subject="rule documents",
                detail=(
                    f"{rules_report.documents_with_issues} document(s) "
                    "with issue(s)."
                ),
            )
        )
    if recipe_report is not None and not recipe_report.passed():
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="error",
                category="recipe",
                subject="recipe templates",
                detail=f"{len(recipe_report.violations)} violation(s) detected.",
            )
        )
    if (
        recipes_dir.is_dir()
        and recipe_report is not None
        and recipe_report.recipes_discovered == 0
    ):
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="attention",
                category="recipe",
                subject="workspace recipes",
                detail="No recipe manifests were discovered.",
            )
        )

    return domain.WorkspaceHealthReport(
        project_root=project_root,
        config_path=config_path,
        config_present=config_present,
        target_dir_present=target_dir.is_dir(),
        rules_dir_present=rules_dir.is_dir(),
        local_rules_dir_present=local_rules_dir.is_dir(),
        shared_rules_dir_present=shared_rules_dir.is_dir(),
        recipes_dir_present=recipes_dir.is_dir(),
        rules_report=rules_report,
        recipe_report=recipe_report,
        findings=tuple(findings),
    )


def _filesystem_findings(
    *,
    target_dir_present: bool,
    rules_dir_present: bool,
    local_rules_dir_present: bool,
    shared_rules_dir_present: bool,
) -> tuple[domain.WorkspaceHealthFinding, ...]:
    findings: list[domain.WorkspaceHealthFinding] = []
    checks = (
        (target_dir_present, "workspace", ".enclosure directory"),
        (rules_dir_present, "rules", "rules directory"),
        (local_rules_dir_present, "rules", "local rules directory"),
        (shared_rules_dir_present, "rules", "shared rules directory"),
    )
    for present, category, subject in checks:
        if present:
            continue
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="error",
                category=category,
                subject=subject,
                detail="Required workspace path is missing.",
            )
        )
    return tuple(findings)


__all__ = [
    "build_workspace_health_report",
]
