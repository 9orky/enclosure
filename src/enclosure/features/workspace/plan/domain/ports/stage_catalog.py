from __future__ import annotations

from typing import Protocol

from .. import stage


class StageCatalog(Protocol):
    def load_stages(self) -> list[stage.PlanningStage]:
        ...


__all__ = ["StageCatalog"]
