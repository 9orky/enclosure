from __future__ import annotations

from pathlib import Path

from enclosure.features.workspace.plan import domain
from enclosure.features.workspace.plan.application.plan_application import PlanApplication
from enclosure.features.workspace.plan.infrastructure import (
    DEFAULT_DATABASE_NAME,
    EventsourcingSQLitePersistence,
)


def test_workspace_sqlite_persistence_builds_explicit_package_environment(
    tmp_path: Path,
) -> None:
    persistence = EventsourcingSQLitePersistence.for_workspace_cache(tmp_path)

    env = persistence.environment()

    assert persistence.database_path == tmp_path / DEFAULT_DATABASE_NAME
    assert env == {
        "PERSISTENCE_MODULE": "eventsourcing.sqlite",
        "SQLITE_DBNAME": str(tmp_path / DEFAULT_DATABASE_NAME),
        "CREATE_TABLE": "yes",
    }


def test_workspace_sqlite_persistence_creates_file_database_tables(
    tmp_path: Path,
) -> None:
    persistence = EventsourcingSQLitePersistence.for_workspace_cache(tmp_path)
    app = PlanApplication(env=persistence.environment())

    plan = app.create_plan("File Database")
    loaded = app.get_plan(domain.PlanId(plan.id))

    assert loaded.title == "File Database"
    assert persistence.database_path.is_file()


def test_workspace_sqlite_persistence_supports_in_memory_database() -> None:
    persistence = EventsourcingSQLitePersistence.in_memory()
    app = PlanApplication(env=persistence.environment())

    plan = app.create_plan("Memory Database")
    status = app.plan_status(
        project_root=persistence.database_path,
        database_path=persistence.database_path,
    )

    assert str(persistence.database_path) == ":memory:"
    assert status.current_plan_id == str(plan.id)
    assert status.title == "Memory Database"
