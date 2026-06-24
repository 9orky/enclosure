from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Enrichment:
    slot_id: str
    values: dict[str, Any]


__all__ = ["Enrichment"]
