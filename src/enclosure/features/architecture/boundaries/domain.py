from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from modwire.architecture import EdgeRuleViolation, FlowViolation

from enclosure.shared import architecture


@dataclass(frozen=True)
class BoundariesReport:
    project_root: Path
    config_path: Path
    config_format: str
    language: str
    runtime_command: str = ""
    files_found: int = 0
    files_excluded: int = 0
    files_checked: int = 0
    violations: tuple[EdgeRuleViolation | FlowViolation, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            **architecture.metadata_json(self),
            "violations": [asdict(violation) for violation in self.violations],
        }


__all__ = [
    "BoundariesReport",
]
