from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from eventsourcing.domain import DomainEvent

from enclosure.features.workspace.plan import domain


def _replay(events: Sequence[DomainEvent]) -> object:
    aggregate: object | None = None
    for stored_event in events:
        aggregate = stored_event.mutate(aggregate)
    if aggregate is None:
        raise AssertionError("No aggregate was reconstructed")
    return aggregate


def test_plan_reconstructs_workflow_state_from_decorated_events() -> None:
    plan = domain.Plan(
        title="Replay Plan",
        current_stage=domain.PlanState.DRAFT.value,
        source_use_case_id="manual",
        source_plan_item_id="manual",
        created_by_command="test",
        schema_version=1,
    )

    plan.accept_stage_output(
        "draft",
        "plan",
        [{"id": "draft", "stable_identity": "draft", "values": {}}],
        [{"id": "draft:plan", "upstream_identity": "draft", "stage_id": "plan"}],
    )
    plan.advance_stage("plan", domain.PlanState.ACTIVE, "Accepted draft")
    plan.ask_question(
        "draft:draft-md:ready",
        "Ready?",
        "The draft is ready.",
        True,
        "draft",
    )
    plan.answer_question(
        "draft:draft-md:ready",
        "Ready?",
        "The draft is ready.",
        "The draft is ready.",
        "draft",
    )
    plan.record_projection("plan-hash", "PLAN.md", "plan", "# Plan\n")
    plan.request_roll("workspace plan roll", "plan")
    plan.close("Done", "workspace plan close")

    reconstructed = _replay(plan.collect_events())

    assert isinstance(reconstructed, domain.Plan)
    assert reconstructed.title == "Replay Plan"
    assert reconstructed.current_stage == domain.PlanState.COMPLETE.value
    assert reconstructed.state == domain.PlanState.COMPLETE
    assert not reconstructed.active
    assert reconstructed.questions["draft:draft-md:ready"].status == (
        domain.QuestionStatus.RESOLVED
    )
    assert reconstructed.questions["draft:draft-md:ready"].answer == (
        "The draft is ready."
    )
    assert reconstructed.stage_outputs["draft"]["next_stage"] == "plan"


def test_plan_registry_reconstructs_active_plan_from_decorated_events() -> None:
    plan_id = domain.PlanId(UUID("11111111-1111-4111-8111-111111111111"))
    registry = domain.PlanRegistry(id=domain.PLAN_REGISTRY_ID)

    registry.activate_plan(plan_id)
    activated_events = registry.collect_events()

    active = _replay(activated_events)

    assert isinstance(active, domain.PlanRegistry)
    assert active.active_plan_id() == plan_id

    active.release_plan(plan_id, "completed")
    release_events = active.collect_events()

    released = _replay([*activated_events, *release_events])

    assert isinstance(released, domain.PlanRegistry)
    try:
        released.active_plan_id()
    except LookupError:
        pass
    else:
        raise AssertionError("Released registry should not expose an active plan")


def test_plan_reconstructs_asked_and_answered_questions_from_events() -> None:
    plan = domain.Plan(
        title="Question Plan",
        current_stage=domain.PlanState.DRAFT.value,
        source_use_case_id="manual",
        source_plan_item_id="manual",
        created_by_command="test",
        schema_version=1,
    )

    plan.ask_question(
        "draft:draft-md:scope",
        "Scope?",
        "The scope must be clear.",
        True,
        "draft",
    )
    plan.answer_question(
        "draft:draft-md:scope",
        "Scope?",
        "The scope must be clear.",
        "The scope is draft only.",
        "draft",
    )

    reconstructed = _replay(plan.collect_events())

    assert isinstance(reconstructed, domain.Plan)
    question = reconstructed.questions["draft:draft-md:scope"]
    assert question.text == "Scope?"
    assert question.explanation == "The scope must be clear."
    assert question.answer == "The scope is draft only."
    assert question.status == domain.QuestionStatus.RESOLVED
    assert not question.blocking
