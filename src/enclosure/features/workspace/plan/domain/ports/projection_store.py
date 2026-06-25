from __future__ import annotations

from typing import Protocol

from .. import stage_data


class ProjectionStore(Protocol):
    def read_text(self, path: str) -> str:
        ...

    def write_projection(
        self,
        artifact: stage_data.ProjectedArtifact,
    ) -> None:
        ...


__all__ = ["ProjectionStore"]
