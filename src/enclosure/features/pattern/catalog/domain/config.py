from __future__ import annotations

from pydantic import Field, field_validator

from enclosure.shared import config


class PatternConfig(config.StrictConfigModel):
    skip: tuple[str, ...]
    roles_map: dict[str, str] = Field(default_factory=dict)

    @field_validator("skip")
    @classmethod
    def normalize_skip_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(value.strip().replace("\\", "/") for value in values if value.strip())

    @field_validator("roles_map")
    @classmethod
    def normalize_roles_map(cls, values: dict[str, str]) -> dict[str, str]:
        return {
            module_name.strip().replace("\\", "/"): role_name.strip()
            for module_name, role_name in values.items()
            if module_name.strip() and role_name.strip()
        }


__all__ = ["PatternConfig"]
