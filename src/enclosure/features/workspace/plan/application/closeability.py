from __future__ import annotations

from dataclasses import dataclass

from enclosure.features.architecture import health as architecture_health

from .. import domain


@dataclass(frozen=True)
class PlanCloseabilityReport:
    closeable: bool
    blockers: tuple[str, ...]


def evaluate_plan_closeability(plan: domain.Plan) -> PlanCloseabilityReport:
    blockers: list[str] = []
    if not plan.active:
        blockers.append("Plan is not active")
    blockers.extend(_architecture_contract_blockers())
    return PlanCloseabilityReport(
        closeable=not blockers,
        blockers=tuple(blockers),
    )


def require_plan_closeable(plan: domain.Plan) -> None:
    report = evaluate_plan_closeability(plan)
    if report.closeable:
        return
    raise ValueError(
        "Plan is not closeable until the architecture contract matches "
        "implementation 100%: " + "; ".join(report.blockers)
    )


def _architecture_contract_blockers() -> tuple[str, ...]:
    try:
        report = architecture_health.build_health_report()
    except Exception as exc:
        return (f"architecture health: {exc}",)
    return tuple(
        f"{finding.category}: {finding.detail}" for finding in report.blocking_findings
    )


__all__ = [
    "PlanCloseabilityReport",
    "evaluate_plan_closeability",
    "require_plan_closeable",
]
