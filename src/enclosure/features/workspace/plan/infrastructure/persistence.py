from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_DATABASE_NAME = "plans.sqlite"


@dataclass(frozen=True)
class EventsourcingSQLitePersistence:
    database_path: Path
    create_table: bool = True

    @classmethod
    def for_workspace_cache(
        cls,
        cache_dir: Path,
    ) -> EventsourcingSQLitePersistence:
        return cls(database_path=cache_dir / DEFAULT_DATABASE_NAME)

    @classmethod
    def in_memory(cls) -> EventsourcingSQLitePersistence:
        return cls(database_path=Path(":memory:"))

    def environment(self) -> dict[str, str]:
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "PERSISTENCE_MODULE": "eventsourcing.sqlite",
            "SQLITE_DBNAME": str(self.database_path),
            "CREATE_TABLE": "yes" if self.create_table else "no",
        }


__all__ = [
    "DEFAULT_DATABASE_NAME",
    "EventsourcingSQLitePersistence",
]
