from __future__ import annotations

from dataclasses import replace

from .. import domain
from . import closeability, plan_application, runtime


PlanStatusReport = plan_application.PlanStatusReport


def plan_status() -> PlanStatusReport:
    plan_runtime = runtime.current_runtime()
    plan_app = runtime.current_plan_application(plan_runtime)
    report = plan_app.plan_status(
        project_root=plan_runtime.project_root,
        database_path=plan_runtime.database_path,
    )
    if not report.current_plan_id:
        return report
    close_report = closeability.evaluate_plan_closeability(plan_app.get_active_plan())
    return replace(
        report,
        closeable=close_report.closeable,
        close_blockers=close_report.blockers,
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
