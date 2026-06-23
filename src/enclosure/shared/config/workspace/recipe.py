from __future__ import annotations

from fnmatch import fnmatch

from pydantic import Field
from pydantic import field_validator

from ..base import StrictConfigModel


class RecipeConfig(StrictConfigModel):
    skip: tuple[str, ...] = ()
    roles_map: dict[str, str] = Field(default_factory=dict)

    @property
    def skip_globs(self) -> tuple[str, ...]:
        return self.skip

    @field_validator("skip")
    @classmethod
    def normalize_skip_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            value.strip().replace("\\", "/")
            for value in values
            if value.strip()
        )

    @field_validator("roles_map")
    @classmethod
    def normalize_roles_map(cls, values: dict[str, str]) -> dict[str, str]:
        return {
            module_name.strip().replace("\\", "/"): role_name.strip()
            for module_name, role_name in values.items()
            if module_name.strip() and role_name.strip()
        }

    def should_skip(self, relative_path: object) -> bool:
        if hasattr(relative_path, "as_posix"):
            relative_path_text = relative_path.as_posix()
        else:
            relative_path_text = str(relative_path).replace("\\", "/")
        return any(fnmatch(relative_path_text, pattern) for pattern in self.skip)


__all__ = ["RecipeConfig"]
