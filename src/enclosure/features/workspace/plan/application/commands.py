from __future__ import annotations

from pathlib import PurePosixPath

from .. import domain
from . import plan_application, projections, runtime


def start_plan(title: str) -> domain.Plan:
    if not title.strip():
        raise ValueError("Plan title is required")
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    plan = plan_app.create_plan(title)
    stage = domain.DraftStage()
    stage_input = domain.StageInput(
        stage_id=stage.stage_id(),
        data_objects=[
            domain.StageData(
                id="plan",
                stable_identity="plan",
                values={"title": title.strip()},
            )
        ],
    )
    projection = stage.scaffold(stage_input)
    projections.record_stage_projection(plan_runtime, plan, projection)
    plan_app.save(plan)
    projections.write_stage_projection(plan_runtime, plan, projection)
    return plan_app.get_plan(domain.PlanId(plan.id))


def advance_plan() -> domain.Plan:
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    return _advance_plan(plan_runtime, plan_app)


def _advance_plan(
    plan_runtime: runtime._Runtime,
    plan_app: plan_application.PlanApplication,
) -> domain.Plan:
    plan = plan_app.get_active_plan()
    if plan.current_stage == domain.PlanState.COMPLETE.value:
        return plan
    registry = runtime.stage_registry()
    stage = registry.current_for(plan)
    projection = projections.read_stage_projection(plan_runtime, plan, stage)
    questions = projections.record_projection_questions(plan_app, plan, projection)
    blocking_questions = domain.blocking_questions(questions)
    if blocking_questions:
        raise ValueError(
            "Blocking open questions prevent stage advance: "
            + ", ".join(question.id for question in blocking_questions)
        )
    if not domain.question_cycle_passed(questions):
        raise ValueError(
            "A resolved question is required before stage advance: "
            f"{stage.stage_id()}"
        )
    review = stage.parse_review(projection)
    validation = stage.validate_review(review)
    if not validation.valid:
        raise ValueError("; ".join(validation.messages))
    result = stage.accept(review)
    plan.accept_stage_output(
        result.output.stage_id,
        result.output.next_stage_id,
        [
            {
                "id": data_object.id,
                "stable_identity": data_object.stable_identity,
                "values": data_object.values,
            }
            for data_object in result.output.data_objects
        ],
        [
            {
                "id": derived_slot.id,
                "upstream_identity": derived_slot.upstream_identity,
                "stage_id": derived_slot.stage_id,
                "variant_key": derived_slot.variant_key,
            }
            for derived_slot in result.output.derived_slots
        ],
    )
    if result.output.next_stage_id == domain.PlanState.COMPLETE.value:
        plan.advance_stage(
            domain.PlanState.COMPLETE.value,
            domain.PlanState.COMPLETE,
            "Stage loop completed",
        )
        return plan_app.release_active_plan(plan, "Stage loop completed")
    next_stage = registry.next_after(stage)
    next_input = domain.StageInput(
        stage_id=next_stage.stage_id(),
        data_objects=result.output.data_objects,
    )
    plan.advance_stage(
        next_stage.stage_id(),
        domain.PlanState.ACTIVE,
        f"Accepted {stage.stage_id()} and projected {next_stage.stage_id()}",
    )
    plan_app.save(plan)
    plan = plan_app.get_plan(domain.PlanId(plan.id))
    next_projection = next_stage.scaffold(next_input)
    projections.record_stage_projection(plan_runtime, plan, next_projection)
    plan_app.save(plan)
    projections.write_stage_projection(plan_runtime, plan, next_projection)
    return plan_app.get_plan(domain.PlanId(plan.id))


def roll_plan() -> domain.Plan:
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    plan = plan_app.get_active_plan()
    plan.request_roll("workspace plan roll", plan.current_stage)
    plan_app.save(plan)
    plan = plan_app.get_plan(domain.PlanId(plan.id))
    while plan.active:
        plan = _advance_plan(plan_runtime, plan_app)
        if plan.current_stage == domain.PlanState.COMPLETE.value:
            break
    return plan


def put_stage_artifact(path: str, content: str) -> domain.Plan:
    normalized_path = _normalize_artifact_path(path)
    if not content.strip():
        raise ValueError("Artifact content is required")
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    plan = plan_app.get_active_plan()
    stage = runtime.stage_registry().current_for(plan)
    file_model = _declared_file_model(stage, normalized_path)
    artifact = domain.ProjectedArtifact(
        path=normalized_path,
        content=content,
        artifact_kind=file_model.artifact_kind,
    )
    projection = domain.StageProjection(
        stage_id=stage.stage_id(),
        artifacts=[artifact],
    )
    projections.record_stage_projection(plan_runtime, plan, projection)
    plan_app.save(plan)
    projections.write_stage_projection(plan_runtime, plan, projection)
    return plan_app.get_plan(domain.PlanId(plan.id))


def answer_stage_question(title: str, answer: str) -> domain.Plan:
    if not title.strip():
        raise ValueError("Question title is required")
    if not answer.strip():
        raise ValueError("Question answer is required")
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    plan = plan_app.get_active_plan()
    stage = runtime.stage_registry().current_for(plan)
    projection = projections.read_stage_projection(plan_runtime, plan, stage)
    artifact = _question_target_artifact(projection)
    content = _append_answered_question(
        artifact.content,
        title.strip(),
        answer.strip(),
    )
    return put_stage_artifact(artifact.path, content)


def close_plan(reason: str) -> domain.Plan:
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    plan = plan_app.get_active_plan()
    plan.close(
        reason.strip() or "Closed by workspace plan close",
        "workspace plan close",
    )
    return plan_app.release_active_plan(plan, "workspace plan close")


def _normalize_artifact_path(path: str) -> str:
    stripped = path.strip()
    if not stripped:
        raise ValueError("Artifact path is required")
    pure_path = PurePosixPath(stripped)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError("Artifact path must stay inside the active plan")
    return pure_path.as_posix()


def _declared_file_model(
    stage: domain.PlanningStage,
    path: str,
) -> domain.StageFileModel:
    if not isinstance(stage, domain.StageFileContract):
        raise ValueError("Current stage does not declare file models")
    for file_model in stage.file_models(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    ):
        if file_model.matches_path(path):
            return file_model
    raise ValueError(f"Artifact path is not declared by the current stage: {path}")


def _question_target_artifact(
    projection: domain.StageProjection,
) -> domain.ProjectedArtifact:
    for artifact in projection.artifacts:
        if artifact.artifact_kind == "markdown":
            return artifact
    raise ValueError("Current stage has no markdown artifact for questions")


def _append_answered_question(content: str, title: str, answer: str) -> str:
    lines = [
        content.rstrip(),
        "",
        "## Open Questions",
        "",
        f"### {title}",
        "",
        "This question was resolved through the workspace plan CLI.",
        "",
        "#### Answer",
        "",
        answer,
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "advance_plan",
    "answer_stage_question",
    "close_plan",
    "put_stage_artifact",
    "roll_plan",
    "start_plan",
]
