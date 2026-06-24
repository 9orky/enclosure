from __future__ import annotations

from . import plan, stage
from .stages import DraftStage, EpicsStage, PlanStage


class StageRegistry:
    def __init__(
        self,
        stages: list[stage.PlanningStage],
    ) -> None:
        self._stages = {
            planning_stage.stage_id(): planning_stage for planning_stage in stages
        }
        self._order = [planning_stage.stage_id() for planning_stage in stages]

    @classmethod
    def default(cls) -> StageRegistry:
        return cls(stages=[DraftStage(), PlanStage(), EpicsStage()])

    def current_for(self, current_plan: plan.Plan) -> stage.PlanningStage:
        return self._stages[current_plan.current_stage]

    def next_after(
        self,
        planning_stage: stage.PlanningStage,
    ) -> stage.PlanningStage:
        current_index = self._order.index(planning_stage.stage_id())
        return self._stages[self._order[current_index + 1]]

    def register(self, planning_stage: stage.PlanningStage) -> None:
        stage_id = planning_stage.stage_id()
        if stage_id not in self._order:
            self._order.append(stage_id)
        self._stages[stage_id] = planning_stage


__all__ = ["StageRegistry"]
