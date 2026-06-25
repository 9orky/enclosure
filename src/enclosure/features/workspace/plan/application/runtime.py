from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from enclosure.shared.config import settings

from .. import domain, infrastructure
from .event_store import PlanEventStore


@dataclass(frozen=True)
class _Runtime:
    project_root: Path
    database_path: Path


def current_runtime() -> _Runtime:
    if not settings.metadata.target_dir.is_dir():
        raise RuntimeError(
            "Could not find .enclosure/. Run `enclosure workspace sync init` first."
        )
    return _Runtime(
        project_root=settings.metadata.project_root,
        database_path=settings.metadata.cache_dir / "plans.sqlite",
    )


def event_store(runtime: _Runtime) -> PlanEventStore:
    persistence = infrastructure.EventsourcingSQLitePersistence(runtime.database_path)
    return PlanEventStore(env=persistence.environment())


def projection_store(
    runtime: _Runtime,
    plan: domain.Plan,
) -> infrastructure.FilesystemProjectionStore:
    return infrastructure.FilesystemProjectionStore(root=plan_root(runtime, plan))


def stage_registry() -> domain.StageRegistry:
    return domain.StageRegistry(
        stages=infrastructure.FilesystemStageCatalog().load_stages()
    )


def plan_root(runtime: _Runtime, plan: domain.Plan) -> Path:
    slug = "-".join(
        "".join(
            character.lower() if character.isalnum() else " "
            for character in plan.title
        ).split()
    )
    return runtime.project_root / ".enclosure" / "plans" / (slug or "plan")


__all__ = [
    "current_runtime",
    "event_store",
    "plan_root",
    "projection_store",
    "stage_registry",
]
