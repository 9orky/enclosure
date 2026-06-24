from __future__ import annotations

from typing import Protocol

from .. import plan, stage_data


class ProjectionStore(Protocol):
    def read_text(self, path: str) -> str:
        ...

    def write_projection(
        self,
        artifact: stage_data.ProjectedArtifact,
    ) -> plan.ProjectionRecord:
        ...

    def content_hash(self, content: str) -> str:
        ...


__all__ = ["ProjectionStore"]
