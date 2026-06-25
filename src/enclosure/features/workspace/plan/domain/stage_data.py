from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from . import questions


@dataclass(frozen=True)
class StageData:
    id: str
    stable_identity: str
    values: dict[str, Any]


@dataclass(frozen=True)
class StageFileModel:
    path: str
    artifact_kind: str
    model_kind: str
    native_schema_source: bool

    def matches_path(self, path: str) -> bool:
        if "{" not in self.path:
            return self.path == path
        pattern = re.escape(self.path)
        pattern = re.sub(r"\\\{[^}]+\\\}", r"[^/]+", pattern)
        return re.fullmatch(pattern, path) is not None


@dataclass(frozen=True)
class DerivedSlot:
    id: str
    upstream_identity: str
    stage_id: str
    variant_key: str


@dataclass(frozen=True)
class StageInput:
    stage_id: str
    data_objects: list[StageData]


@dataclass(frozen=True)
class StageOutput:
    stage_id: str
    next_stage_id: str
    data_objects: list[StageData]
    derived_slots: list[DerivedSlot]


@dataclass(frozen=True)
class ProjectedArtifact:
    path: str
    content: str
    artifact_kind: str


@dataclass(frozen=True)
class StageProjection:
    stage_id: str
    artifacts: list[ProjectedArtifact]


@dataclass(frozen=True)
class AgentContext:
    stage_id: str
    file_models: list[StageFileModel]


@dataclass(frozen=True)
class ReviewData:
    stage_id: str
    values: dict[str, Any]


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    messages: list[str]


@dataclass(frozen=True)
class DriftReport:
    messages: list[str]


@dataclass(frozen=True)
class StageResult:
    status: str
    output: StageOutput
    artifacts: list[ProjectedArtifact]
    questions: list[questions.OpenQuestion]
    drift: DriftReport


@dataclass(frozen=True)
class NativeSchemas:
    flows_mermaid: str
    uml_mermaid: str
    tree_mermaid: str


__all__ = [
    "AgentContext",
    "DerivedSlot",
    "DriftReport",
    "NativeSchemas",
    "ProjectedArtifact",
    "ReviewData",
    "StageData",
    "StageFileModel",
    "StageInput",
    "StageOutput",
    "StageProjection",
    "StageResult",
    "ValidationResult",
]
