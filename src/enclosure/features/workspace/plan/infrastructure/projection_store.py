from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from .. import domain


@dataclass(frozen=True)
class FilesystemProjectionStore:
    root: Path

    def read_text(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8")

    def write_text(self, path: str, content: str) -> None:
        self.write_projection(
            domain.ProjectedArtifact(
                path=path,
                content=content,
                artifact_kind="markdown",
            )
        )

    def write_projection(
        self,
        artifact: domain.ProjectedArtifact,
    ) -> None:
        target = self.root / artifact.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact.content, encoding="utf-8")

    def tracking_position(self) -> int:
        tracking_path = self._tracking_path()
        if not tracking_path.is_file():
            return 0
        content = tracking_path.read_text(encoding="utf-8").strip()
        return int(content or "0")

    def record_tracking(self, notification_id: int) -> None:
        tracking_path = self._tracking_path()
        tracking_path.parent.mkdir(parents=True, exist_ok=True)
        tracking_path.write_text(str(notification_id), encoding="utf-8")

    def content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _tracking_path(self) -> Path:
        return self.root / ".projection-tracking"


__all__ = ["FilesystemProjectionStore"]
