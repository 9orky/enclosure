from __future__ import annotations

from .. import domain
from .event_store import PlanEventStore
from .runtime import _Runtime, projection_store


def read_stage_projection(
    runtime: _Runtime,
    plan: domain.Plan,
    stage: domain.PlanningStage,
) -> domain.StageProjection:
    store = projection_store(runtime, plan)
    artifacts: list[domain.ProjectedArtifact] = []
    for file_model in stage.file_models(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    ):
        if "{" in file_model.path:
            continue
        artifacts.append(
            domain.ProjectedArtifact(
                path=file_model.path,
                content=store.read_text(file_model.path),
                artifact_kind=file_model.artifact_kind,
            )
        )
    return domain.StageProjection(stage_id=stage.stage_id(), artifacts=artifacts)


def record_projection_questions(
    store: PlanEventStore,
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


__all__ = [
    "read_stage_projection",
    "record_projection_questions",
]
