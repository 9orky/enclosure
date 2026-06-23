from __future__ import annotations

from pathlib import Path

from enclosure.shared.config import settings

from .. import domain


def describe_plan_document(name: str) -> domain.PlanDocument:
    project_root = settings.metadata.project_root
    target_dir = settings.metadata.target_dir
    if not target_dir.is_dir():
        raise RuntimeError(
            "Could not find .enclosure/. Run `enclosure workspace sync init` first."
        )
    plans_root = settings.metadata.plans_dir
    plan_name = domain.PlanName(name)
    return domain.PlanDocument(
        name=plan_name,
        project_root=project_root,
        plans_root=plans_root,
        target_path=plan_name.document_path(plans_root),
        content=domain.render_plan_scaffold(plan_name),
    )


def current_plan_report() -> domain.CurrentPlanReport:
    project_root = settings.metadata.project_root
    target_dir = settings.metadata.target_dir
    if not target_dir.is_dir():
        raise RuntimeError(
            "Could not find .enclosure/. Run `enclosure workspace sync init` first."
        )

    plans_root = settings.metadata.plans_dir
    violations: list[domain.PlanViolation] = []
    if not plans_root.exists():
        return domain.CurrentPlanReport(
            project_root=project_root,
            plans_root=plans_root,
        )
    if not plans_root.is_dir():
        violations.append(
            domain.PlanViolation(
                code="plans_path_not_directory",
                message=".enclosure/plans exists but is not a directory.",
            )
        )
        return domain.CurrentPlanReport(
            project_root=project_root,
            plans_root=plans_root,
            violations=tuple(violations),
        )

    entries = tuple(sorted(plans_root.iterdir(), key=lambda path: path.name))
    plan_folders = tuple(path for path in entries if path.is_dir())
    root_files = tuple(path for path in entries if path.is_file())

    if root_files:
        violations.append(
            domain.PlanViolation(
                code="plan_root_files",
                message="Expected plan files inside the current plan folder, not directly under .enclosure/plans.",
            )
        )
    if len(plan_folders) > 1:
        violations.append(
            domain.PlanViolation(
                code="current_plan_folder_count",
                message="Expected at most one current plan folder under .enclosure/plans.",
            )
        )

    current_folder = plan_folders[0] if len(plan_folders) == 1 else None
    plan_files: tuple[Path, ...] = ()
    current_slug = ""
    if current_folder is not None:
        current_slug = current_folder.name
        plan_files = tuple(
            sorted(
                (
                    path
                    for path in current_folder.iterdir()
                    if path.is_file() and path.suffix == ".md"
                ),
                key=lambda path: path.name,
            )
        )
        if not plan_files:
            violations.append(
                domain.PlanViolation(
                    code="missing_plan_file",
                    message="Current plan folder must contain at least one Markdown plan file.",
                )
            )

    return domain.CurrentPlanReport(
        project_root=project_root,
        plans_root=plans_root,
        current_slug=current_slug,
        plan_files=plan_files,
        violations=tuple(violations),
    )


__all__ = ["current_plan_report", "describe_plan_document"]
