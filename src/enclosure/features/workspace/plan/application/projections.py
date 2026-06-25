from __future__ import annotations

from .. import domain
from . import runtime


def read_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    stage: domain.PlanningStage,
) -> domain.StageProjection:
    store = runtime.projection_store(plan_runtime, plan)
    artifacts: list[domain.ProjectedArtifact] = []
    file_models = stage.file_models(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    )
    for file_model in file_models:
        if "{" in file_model.path:
            continue
        recorded_artifact = _recorded_artifact(plan, stage.stage_id(), file_model)
        artifacts.append(
            domain.ProjectedArtifact(
                path=file_model.path,
                content=_read_text_or_recorded(
                    store,
                    file_model.path,
                    recorded_artifact,
                ),
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
                content=_read_text_or_recorded(
                    store,
                    record.path,
                    record.content,
                ),
                artifact_kind=_artifact_kind_for_path(file_models, record.path),
            )
        )
        artifact_paths.add(record.path)
    return domain.StageProjection(stage_id=stage.stage_id(), artifacts=artifacts)


def _recorded_artifact(
    plan: domain.Plan,
    stage_id: str,
    file_model: domain.StageFileModel,
) -> str:
    for record in reversed(list(plan.projections.values())):
        if record.stage == stage_id and record.path == file_model.path:
            return record.content
    return ""


def _read_text_or_recorded(
    store: domain.ProjectionStore,
    path: str,
    recorded_content: str,
) -> str:
    try:
        return store.read_text(path)
    except FileNotFoundError:
        if recorded_content:
            return recorded_content
        raise


def _artifact_kind_for_path(
    file_models: list[domain.StageFileModel],
    path: str,
) -> str:
    for file_model in file_models:
        if file_model.matches_path(path):
            return file_model.artifact_kind
    raise ValueError(f"Projection path is not declared by the stage file model: {path}")


def record_stage_projection(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
    projection: domain.StageProjection,
) -> None:
    store = runtime.projection_store(plan_runtime, plan)
    for artifact in projection.artifacts:
        projection_id = store.content_hash(artifact.content)
        plan.record_projection(
            projection_id,
            artifact.path,
            projection.stage_id,
            artifact.content,
        )
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


def restore_recorded_projections(
    plan_runtime: runtime._Runtime,
    plan: domain.Plan,
) -> None:
    store = runtime.projection_store(plan_runtime, plan)
    for record in plan.projections.values():
        if not record.content:
            continue
        store.write_projection(
            domain.ProjectedArtifact(
                path=record.path,
                content=record.content,
                artifact_kind="markdown",
            )
        )


__all__ = [
    "read_stage_projection",
    "record_stage_projection",
    "restore_recorded_projections",
    "write_stage_projection",
]
