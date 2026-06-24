from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EventsourcingSQLitePersistence:
    database_path: Path

    def environment(self) -> dict[str, str]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "PERSISTENCE_MODULE": "eventsourcing.sqlite",
            "SQLITE_DBNAME": str(self.database_path),
        }


__all__ = ["EventsourcingSQLitePersistence"]
