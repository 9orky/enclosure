from __future__ import annotations

from .. import domain
from . import plan_application, runtime


def read_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    stage: domain.PlanningStage,
) -> domain.StageProjection:
    store = runtime.projection_store(plan_runtime, plan)
    artifacts: list[domain.ProjectedArtifact] = []
    artifact_kinds: dict[str, str] = {}
    for file_model in stage.file_models(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    ):
        artifact_kinds[file_model.path] = file_model.artifact_kind
        if "{" in file_model.path:
            continue
        artifacts.append(
            domain.ProjectedArtifact(
                path=file_model.path,
                content=store.read_text(file_model.path),
                artifact_kind=file_model.artifact_kind,
            )
        )
    artifact_paths = {artifact.path for artifact in artifacts}
    for record in plan.projections.values():
        if record.stage != stage.stage_id() or record.path in artifact_paths:
            continue
        artifacts.append(
            domain.ProjectedArtifact(
                path=record.path,
                content=store.read_text(record.path),
                artifact_kind=artifact_kinds.get(
                    record.path,
                    _artifact_kind_from_path(record.path),
                ),
            )
        )
        artifact_paths.add(record.path)
    return domain.StageProjection(stage_id=stage.stage_id(), artifacts=artifacts)


def _artifact_kind_from_path(path: str) -> str:
    if path.endswith(".mermaid"):
        return "mermaid"
    if path.endswith(".md"):
        return "markdown"
    return "text"


def record_projection_questions(
    store: plan_application.PlanApplication,
    plan: domain.Plan,
    projection: domain.StageProjection,
) -> list[domain.OpenQuestion]:
    questions = domain.extract_open_questions(projection)
    for question in questions:
        plan.change_question(
            question.id,
            question.text,
            question.explanation,
            question.status,
            question.blocking,
            question.revisit_stage,
        )
    if questions:
        store.save(plan)
    return questions


def record_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    projection: domain.StageProjection,
) -> None:
    store = runtime.projection_store(plan_runtime, plan)
    for artifact in projection.artifacts:
        projection_id = store.content_hash(artifact.content)
        plan.record_projection(projection_id, artifact.path, projection.stage_id)
        if artifact.path == "DRAFT.md":
            plan.update_draft(projection_id, artifact.path)


def write_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    projection: domain.StageProjection,
) -> None:
    store = runtime.projection_store(plan_runtime, plan)
    for artifact in projection.artifacts:
        store.write_projection(artifact)


__all__ = [
    "read_stage_projection",
    "record_projection_questions",
    "record_stage_projection",
    "write_stage_projection",
]
