from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from code_map.architecture import EdgeRuleViolation, FlowViolation, supported_analyzers
from pydantic import Field, field_validator

from enclosure.shared import architecture, config


class BoundaryRule(config.StrictConfigModel):
    source: str
    disallow: list[str]
    allow: list[str]
    allow_same_match: bool


class ConfigTagRule(config.StrictConfigModel):
    name: str
    match: str
    except_: list[str] = Field(alias="except")
    exclude: list[str]

    @property
    def excluded_patterns(self) -> tuple[str, ...]:
        return (*self.except_, *self.exclude)


class FlowRuleSet(config.StrictConfigModel):
    layers: list[str]
    module_tag: str
    analyzers: list[str]

    @field_validator("analyzers")
    @classmethod
    def known_analyzers(cls, values: list[str]) -> list[str]:
        unknown = sorted(set(values) - set(supported_analyzers()))
        if unknown:
            raise ValueError(f"unsupported flow analyzer(s): {', '.join(unknown)}")
        return values


class BoundariesConfig(config.StrictConfigModel):
    tags: list[ConfigTagRule]
    rules: list[BoundaryRule]
    flow: FlowRuleSet

    @property
    def boundaries(self) -> list[BoundaryRule]:
        return self.rules


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
    "BoundariesConfig",
    "BoundariesReport",
    "BoundaryRule",
    "ConfigTagRule",
    "FlowRuleSet",
]
