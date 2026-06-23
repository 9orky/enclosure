from __future__ import annotations

from .. import recipe, rules
from enclosure.shared.config import settings

from . import domain


def build_workspace_health_report() -> domain.WorkspaceHealthReport:
    project_root = settings.metadata.project_root
    target_dir = settings.metadata.target_dir
    rules_dir = settings.metadata.rules_dir
    local_rules_dir = settings.metadata.local_rules_dir
    shared_rules_dir = rules_dir / "shared"
    recipes_dir = settings.metadata.recipes_dir

    findings: list[domain.WorkspaceHealthFinding] = []
    config_path = settings.metadata.canonical_config_path
    config_present = False

    try:
        settings.query("workspace")
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
        rules_report = rules.build_rule_schema_report()
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
        recipe_report = recipe.check_recipes(
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

    recipe_drift_report = None
    try:
        recipe_drift_report = recipe.check_recipe_drifts(
            recipe_root=recipes_dir,
        )
    except Exception:
        recipe_drift_report = None

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
    if recipe_drift_report is not None and recipe_drift_report.has_drifts():
        drift_count = sum(
            1 for drift in recipe_drift_report.drifts if drift.has_drift()
        )
        findings.append(
            domain.WorkspaceHealthFinding(
                severity="attention",
                category="recipe-drift",
                subject="mapped recipe modules",
                detail=f"{drift_count} module(s) drift from configured recipes.",
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
        recipe_drift_report=recipe_drift_report,
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
