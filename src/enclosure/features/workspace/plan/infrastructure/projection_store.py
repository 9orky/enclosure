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

    def content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


__all__ = ["FilesystemProjectionStore"]
