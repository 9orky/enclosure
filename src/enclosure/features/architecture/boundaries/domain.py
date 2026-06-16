from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from modwire.architecture import EdgeRuleViolation, FlowViolation, supported_analyzers
from pydantic import Field, field_validator, model_validator

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


class FlowRealmRule(config.StrictConfigModel):
    name: str
    module_tag: str
    layers: list[str] | None = None


class FlowRuleSet(config.StrictConfigModel):
    layers: list[str] = Field(default_factory=list)
    module_tag: str = ""
    module_tags: list[str] = Field(default_factory=list)
    realms: list[FlowRealmRule] = Field(default_factory=list)
    analyzers: list[str] = Field(default_factory=list)

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

    @model_validator(mode="after")
    def tag_names_are_unique(self) -> BoundariesConfig:
        counts = Counter(rule.name for rule in self.tags)
        duplicates = tuple(sorted(name for name, count in counts.items() if count > 1))
        if duplicates:
            names = ", ".join(duplicates)
            raise ValueError(f"duplicate architecture boundary tag name(s): {names}")
        return self


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
    "FlowRealmRule",
    "FlowRuleSet",
]
