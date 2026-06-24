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
        app = self._planning_application()
        plan = app.create_plan(title)
        stage = domain.DraftStage()
        stage_input = domain.StageInput(
            stage_id=stage.stage_id(),
            data_objects=[
                domain.StageData(
                    id="plan",
                    stable_identity="plan",
                    values={"title": title.strip()},
                )
            ],
        )
        projection = stage.scaffold(stage_input)
        store = self._projection_store(plan)
        for artifact in projection.artifacts:
            record = store.write_projection(artifact)
            plan.record_projection(record.id, record.path, stage.stage_id())
            if artifact.path == "DRAFT.md":
                plan.update_draft(record.id, artifact.path)
        app.save(plan)
        return app.get_plan(domain.PlanId(plan.id))

    def next(self) -> domain.Plan:
        app = self._planning_application()
        plan = app.get_active_plan()
        if plan.current_stage == domain.PlanState.COMPLETE.value:
            return plan
        registry = self._stage_registry()
        stage = registry.current_for(plan)
        projection = self._read_stage_projection(plan, stage)
        review = stage.parse_review(projection)
        validation = stage.validate_review(review)
        if not validation.valid:
            raise ValueError("; ".join(validation.messages))
        result = stage.accept(review)
        plan.accept_stage_output(
            result.output.stage_id,
            result.output.next_stage_id,
            tuple(
                {
                    "id": data_object.id,
                    "stable_identity": data_object.stable_identity,
                    "values": data_object.values,
                }
                for data_object in result.output.data_objects
            ),
            tuple(
                {
                    "id": derived_slot.id,
                    "upstream_identity": derived_slot.upstream_identity,
                    "stage_id": derived_slot.stage_id,
                    "variant_key": derived_slot.variant_key,
                }
                for derived_slot in result.output.derived_slots
            ),
        )
        if result.output.next_stage_id == domain.PlanState.COMPLETE.value:
            plan.advance_stage(
                domain.PlanState.COMPLETE.value,
                domain.PlanState.COMPLETE,
                "Stage loop completed",
            )
            app.save(plan)
            return app.get_plan(domain.PlanId(plan.id))
        next_stage = registry.next_after(stage)
        next_input = domain.StageInput(
            stage_id=next_stage.stage_id(),
            data_objects=result.output.data_objects,
        )
        store = self._projection_store(plan)
        for artifact in next_stage.scaffold(next_input).artifacts:
            record = store.write_projection(artifact)
            plan.record_projection(record.id, record.path, next_stage.stage_id())
        plan.advance_stage(
            next_stage.stage_id(),
            domain.PlanState.ACTIVE,
            f"Accepted {stage.stage_id()} and projected {next_stage.stage_id()}",
        )
        app.save(plan)
        return app.get_plan(domain.PlanId(plan.id))

    def agent(self) -> domain.AgentContext:
        plan = self._planning_application().get_active_plan()
        stage = self._stage_registry().current_for(plan)
        return stage.agent_context(
            domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
        )

    def roll(self) -> domain.Plan:
        app = self._planning_application()
        plan = app.get_active_plan()
        plan.request_roll("workspace plan roll", plan.current_stage)
        app.save(plan)
        plan = app.get_plan(domain.PlanId(plan.id))
        while plan.active:
            plan = self.next()
            if plan.current_stage == domain.PlanState.COMPLETE.value:
                break
        return plan

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

    def _projection_store(self, plan: domain.Plan) -> infrastructure.FilesystemProjectionStore:
        return infrastructure.FilesystemProjectionStore(root=self._plan_root(plan))

    def _stage_registry(self) -> domain.StageRegistry:
        return domain.StageRegistry(
            stages=infrastructure.FilesystemStageCatalog().load_stages()
        )

    def _read_stage_projection(
        self,
        plan: domain.Plan,
        stage: domain.PlanningStage,
    ) -> domain.StageProjection:
        store = self._projection_store(plan)
        artifacts: list[domain.ProjectedArtifact] = []
        for file_model in stage.file_models(
            domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
        ):
            if "{" in file_model.path:
                continue
            artifacts.append(
                domain.ProjectedArtifact(
                    path=file_model.path,
                    content=store.read_text(file_model.path),
                    artifact_kind=file_model.artifact_kind,
                )
            )
        return domain.StageProjection(stage_id=stage.stage_id(), artifacts=artifacts)

    def _plan_root(self, plan: domain.Plan) -> Path:
        slug = "-".join(
            "".join(
                character.lower() if character.isalnum() else " "
                for character in plan.title
            ).split()
        )
        return self._project_root / ".enclosure" / "plans" / (slug or "plan")


__all__ = [
    "PlanStatusReport",
    "WorkspacePlanModule",
]
