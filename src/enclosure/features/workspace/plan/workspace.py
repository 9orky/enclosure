from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from enclosure.shared.config import settings

from . import application, domain, infrastructure


@dataclass(frozen=True)
class PlanStatusReport:
    project_root: Path
    database_path: Path
    current_plan_id: str
    title: str
    current_stage: str
    state: str
    active: bool
    version: int
    question_count: int
    projection_count: int


class WorkspacePlanModule:
    def __init__(self, project_root: Path, database_path: Path) -> None:
        self._project_root = Path(project_root)
        self._database_path = Path(database_path)
        self._persistence = infrastructure.EventsourcingSQLitePersistence(
            self._database_path
        )

    @classmethod
    def from_current_workspace(cls) -> WorkspacePlanModule:
        if not settings.metadata.target_dir.is_dir():
            raise RuntimeError(
                "Could not find .enclosure/. Run `enclosure workspace sync init` first."
            )
        return cls(
            project_root=settings.metadata.project_root,
            database_path=settings.metadata.cache_dir / "plans.sqlite",
        )

    def start(self, title: str) -> domain.Plan:
        if not title.strip():
            raise ValueError("Plan title is required")
        return self._planning_application().create_plan(title)

    def status(self) -> PlanStatusReport:
        try:
            plan = self._planning_application().get_active_plan()
        except LookupError:
            return PlanStatusReport(
                project_root=self._project_root,
                database_path=self._database_path,
                current_plan_id="",
                title="",
                current_stage="",
                state="",
                active=False,
                version=0,
                question_count=0,
                projection_count=0,
            )
        return PlanStatusReport(
            project_root=self._project_root,
            database_path=self._database_path,
            current_plan_id=str(plan.id),
            title=plan.title,
            current_stage=plan.current_stage,
            state=plan.state.value,
            active=plan.active,
            version=plan.version,
            question_count=len(plan.questions),
            projection_count=len(plan.projections),
        )

    def _planning_application(self) -> application.PlanningApplication:
        return application.PlanningApplication(env=self._persistence.environment())


__all__ = [
    "PlanStatusReport",
    "WorkspacePlanModule",
]
