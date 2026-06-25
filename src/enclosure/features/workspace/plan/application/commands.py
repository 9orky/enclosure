from __future__ import annotations

from .. import domain
from . import projections, runtime as plan_runtime


def start_plan(title: str) -> domain.Plan:
    if not title.strip():
        raise ValueError("Plan title is required")
    runtime = plan_runtime.current_runtime()
    store = plan_runtime.event_store(runtime)
    plan = store.create_plan(title)
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
    file_store = plan_runtime.projection_store(runtime, plan)
    for artifact in projection.artifacts:
        record = file_store.write_projection(artifact)
        plan.record_projection(record.id, record.path, stage.stage_id())
        if artifact.path == "DRAFT.md":
            plan.update_draft(record.id, artifact.path)
    store.save(plan)
    return store.get_plan(domain.PlanId(plan.id))


def advance_plan() -> domain.Plan:
    runtime = plan_runtime.current_runtime()
    store = plan_runtime.event_store(runtime)
    plan = store.get_active_plan()
    if plan.current_stage == domain.PlanState.COMPLETE.value:
        return plan
    registry = plan_runtime.stage_registry()
    stage = registry.current_for(plan)
    projection = projections.read_stage_projection(runtime, plan, stage)
    questions = projections.record_projection_questions(store, plan, projection)
    blocking_questions = domain.blocking_questions(questions)
    if blocking_questions:
        raise ValueError(
            "Blocking open questions prevent stage advance: "
            + ", ".join(question.id for question in blocking_questions)
        )
    review = stage.parse_review(projection)
    validation = stage.validate_review(review)
    if not validation.valid:
        raise ValueError("; ".join(validation.messages))
    result = stage.accept(review)
    plan.accept_stage_output(
        result.output.stage_id,
        result.output.next_stage_id,
        tuple(
            {
                "id": data_object.id,
                "stable_identity": data_object.stable_identity,
                "values": data_object.values,
            }
            for data_object in result.output.data_objects
        ),
        tuple(
            {
                "id": derived_slot.id,
                "upstream_identity": derived_slot.upstream_identity,
                "stage_id": derived_slot.stage_id,
                "variant_key": derived_slot.variant_key,
            }
            for derived_slot in result.output.derived_slots
        ),
    )
    if result.output.next_stage_id == domain.PlanState.COMPLETE.value:
        plan.advance_stage(
            domain.PlanState.COMPLETE.value,
            domain.PlanState.COMPLETE,
            "Stage loop completed",
        )
        store.save(plan)
        return store.get_plan(domain.PlanId(plan.id))
    next_stage = registry.next_after(stage)
    next_input = domain.StageInput(
        stage_id=next_stage.stage_id(),
        data_objects=result.output.data_objects,
    )
    file_store = plan_runtime.projection_store(runtime, plan)
    for artifact in next_stage.scaffold(next_input).artifacts:
        record = file_store.write_projection(artifact)
        plan.record_projection(record.id, record.path, next_stage.stage_id())
    plan.advance_stage(
        next_stage.stage_id(),
        domain.PlanState.ACTIVE,
        f"Accepted {stage.stage_id()} and projected {next_stage.stage_id()}",
    )
    store.save(plan)
    return store.get_plan(domain.PlanId(plan.id))


def roll_plan() -> domain.Plan:
    runtime = plan_runtime.current_runtime()
    store = plan_runtime.event_store(runtime)
    plan = store.get_active_plan()
    plan.request_roll("workspace plan roll", plan.current_stage)
    store.save(plan)
    plan = store.get_plan(domain.PlanId(plan.id))
    while plan.active:
        plan = advance_plan()
        if plan.current_stage == domain.PlanState.COMPLETE.value:
            break
    return plan


def close_plan(reason: str) -> domain.Plan:
    runtime = plan_runtime.current_runtime()
    store = plan_runtime.event_store(runtime)
    plan = store.get_active_plan()
    plan.close(
        reason.strip() or "Closed by workspace plan close",
        "workspace plan close",
    )
    store.save(plan)
    return store.get_plan(domain.PlanId(plan.id))


__all__ = [
    "advance_plan",
    "close_plan",
    "roll_plan",
    "start_plan",
]
