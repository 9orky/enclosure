from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import domain
from . import runtime as plan_runtime


@dataclass(frozen=True)
class PlanStatusReport:
    project_root: Path
    database_path: Path
    current_plan_id: str
    title: str
    current_stage: str
    state: str
    active: bool
    version: int
    question_count: int
    projection_count: int

def plan_status() -> PlanStatusReport:
    runtime = plan_runtime.current_runtime()
    try:
        plan = plan_runtime.event_store(runtime).get_active_plan()
    except LookupError:
        return PlanStatusReport(
            project_root=runtime.project_root,
            database_path=runtime.database_path,
            current_plan_id="",
            title="",
            current_stage="",
            state="",
            active=False,
            version=0,
            question_count=0,
            projection_count=0,
        )
    return PlanStatusReport(
        project_root=runtime.project_root,
        database_path=runtime.database_path,
        current_plan_id=str(plan.id),
        title=plan.title,
        current_stage=plan.current_stage,
        state=plan.state.value,
        active=plan.active,
        version=plan.version,
        question_count=len(plan.questions),
        projection_count=len(plan.projections),
    )


def agent_context() -> domain.AgentContext:
    runtime = plan_runtime.current_runtime()
    plan = plan_runtime.event_store(runtime).get_active_plan()
    stage = plan_runtime.stage_registry().current_for(plan)
    return stage.agent_context(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    )


__all__ = [
    "agent_context",
    "plan_status",
    "PlanStatusReport",
]
