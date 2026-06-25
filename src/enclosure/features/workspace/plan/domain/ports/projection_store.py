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

    def tracking_position(self) -> int:
        ...

    def record_tracking(self, notification_id: int) -> None:
        ...

    def content_hash(self, content: str) -> str:
        ...


__all__ = ["ProjectionStore"]
