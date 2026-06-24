from __future__ import annotations

from .. import domain


class FilesystemStageCatalog:
    def load_stages(self) -> list[domain.PlanningStage]:
        return [
            domain.DraftStage(),
            domain.PlanStage(),
            domain.EpicsStage(),
        ]


__all__ = ["FilesystemStageCatalog"]
