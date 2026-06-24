from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

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


@dataclass(frozen=True)
class LivePlanReport:
    project_root: Path
    plan_root: Path
    heartbeat_path: Path
    current_plan_id: str
    title: str
    current_stage: str
    state: str
    agent_connected: bool
    review_files: list[str]
    questions: list[domain.OpenQuestion]
    blocking_questions: list[domain.OpenQuestion]


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
        questions = self._record_projection_questions(app, plan, projection)
        blocking_questions = [question for question in questions if question.blocking]
        if blocking_questions:
            raise ValueError(
                "Blocking open questions prevent stage advance: "
                + ", ".join(question.id for question in blocking_questions)
            )
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

    def start_or_resume_live(self, title: str) -> domain.Plan:
        app = self._planning_application()
        try:
            return app.get_active_plan()
        except LookupError:
            return self.start(title)

    def connect_agent(self) -> Path:
        heartbeat_path = self._heartbeat_path()
        heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        heartbeat_path.write_text(str(time.time()), encoding="utf-8")
        return heartbeat_path

    def live_report(self) -> LivePlanReport:
        app = self._planning_application()
        plan = app.get_active_plan()
        stage = self._stage_registry().current_for(plan)
        projection = self._read_stage_projection(plan, stage)
        self._record_projection_questions(app, plan, projection)
        plan = app.get_plan(domain.PlanId(plan.id))
        questions = list(plan.questions.values())
        return LivePlanReport(
            project_root=self._project_root,
            plan_root=self._plan_root(plan),
            heartbeat_path=self._heartbeat_path(),
            current_plan_id=str(plan.id),
            title=plan.title,
            current_stage=plan.current_stage,
            state=plan.state.value,
            agent_connected=self._agent_connected(),
            review_files=[artifact.path for artifact in projection.artifacts],
            questions=questions,
            blocking_questions=[
                question for question in questions if question.blocking
            ],
        )

    def ask_question(self, text: str, explanation: str) -> domain.OpenQuestion:
        if not text.strip():
            raise ValueError("Question text is required")
        app = self._planning_application()
        plan = app.get_active_plan()
        stage = self._stage_registry().current_for(plan)
        target_file = self._primary_stage_file(stage)
        store = self._projection_store(plan)
        content = store.read_text(target_file)
        next_content = domain.append_open_question(content, text, explanation)
        store.write_text(target_file, next_content)
        projection = self._read_stage_projection(plan, stage)
        questions = self._record_projection_questions(app, plan, projection)
        matching = [
            question
            for question in questions
            if question.text == text.strip()
        ]
        if not matching:
            raise RuntimeError("Question was not recorded")
        return matching[-1]

    def answer_question(self, question_id: str, answer: str) -> domain.OpenQuestion:
        if not answer.strip():
            raise ValueError("Answer is required")
        app = self._planning_application()
        plan = app.get_active_plan()
        stage = self._stage_registry().current_for(plan)
        store = self._projection_store(plan)
        for artifact in self._read_stage_projection(plan, stage).artifacts:
            try:
                next_content = domain.append_question_answer(
                    stage.stage_id(),
                    artifact.path,
                    artifact.content,
                    question_id,
                    answer,
                )
            except ValueError:
                continue
            store.write_text(artifact.path, next_content)
            projection = self._read_stage_projection(plan, stage)
            questions = self._record_projection_questions(app, plan, projection)
            matching = [
                question
                for question in questions
                if question.id == question_id
            ]
            if matching:
                return matching[-1]
        raise ValueError(f"Question not found in current stage files: {question_id}")

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

    def _record_projection_questions(
        self,
        app: application.PlanningApplication,
        plan: domain.Plan,
        projection: domain.StageProjection,
    ) -> list[domain.OpenQuestion]:
        questions = domain.extract_open_questions(projection)
        for question in questions:
            plan.change_question(
                question.id,
                question.text,
                question.explanation,
                question.status,
                question.blocking,
                question.revisit_stage,
            )
        if questions:
            app.save(plan)
        return questions

    def _primary_stage_file(self, stage: domain.PlanningStage) -> str:
        for file_model in stage.file_models(
            domain.StageInput(stage_id=stage.stage_id(), data_objects=[])
        ):
            if "{" not in file_model.path:
                return file_model.path
        raise ValueError(f"Stage has no concrete review file: {stage.stage_id()}")

    def _heartbeat_path(self) -> Path:
        return self._database_path.parent / "plan-live" / "agent-heartbeat"

    def _agent_connected(self) -> bool:
        heartbeat_path = self._heartbeat_path()
        if not heartbeat_path.is_file():
            return False
        return time.time() - heartbeat_path.stat().st_mtime < 10

    def _plan_root(self, plan: domain.Plan) -> Path:
        slug = "-".join(
            "".join(
                character.lower() if character.isalnum() else " "
                for character in plan.title
            ).split()
        )
        return self._project_root / ".enclosure" / "plans" / (slug or "plan")


__all__ = [
    "LivePlanReport",
    "PlanStatusReport",
    "WorkspacePlanModule",
]
