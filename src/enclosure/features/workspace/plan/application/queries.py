from __future__ import annotations

from .. import domain
from . import plan_application, runtime


PlanStatusReport = plan_application.PlanStatusReport


def plan_status() -> PlanStatusReport:
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    return plan_app.plan_status(
        project_root=plan_runtime.project_root,
        database_path=plan_runtime.database_path,
    )


def agent_context() -> domain.AgentContext:
    plan_runtime = runtime.current_runtime()
    plan = runtime.current_plan_application(plan_runtime).get_active_plan()
    stage = runtime.stage_registry().current_for(plan)
    return stage.agent_context(
        domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
    )


__all__ = [
    "agent_context",
    "plan_status",
    "PlanStatusReport",
]
