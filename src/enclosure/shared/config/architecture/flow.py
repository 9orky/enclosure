from __future__ import annotations

from modwire.architecture import supported_analyzers
from pydantic import Field
from pydantic import field_validator

from .. import base


class FlowRealmRule(base.StrictConfigModel):
    name: str
    module_tag: str
    layers: list[str] = Field(default_factory=list)


class FlowRuleSet(base.StrictConfigModel):
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


__all__ = ["FlowRealmRule", "FlowRuleSet"]
