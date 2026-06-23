from __future__ import annotations

from enclosure.shared.config import settings

from . import domain, infrastructure


def describe_plan_document(name: str) -> domain.PlanDocument:
    return _build_document(name)


def create_plan_document(name: str, *, force: bool) -> domain.PlanWriteResult:
    return infrastructure.file_plan_materializer.materialize(
        _build_document(name),
        force=force,
    )


def _build_document(name: str) -> domain.PlanDocument:
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


__all__ = [
    "create_plan_document",
    "describe_plan_document",
]
