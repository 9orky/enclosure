from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError
import yaml

ModelT = TypeVar("ModelT", bound=BaseModel)


class ConfigError(RuntimeError):
    pass


class StrictConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def load_yaml_mapping(
    path: Path,
    *,
    label: str,
    error_type: type[Exception],
) -> dict[str, Any]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise error_type(f"Could not read {label.lower()}: {path}") from exc

    try:
        raw_data = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as exc:
        raise error_type(f"Invalid {label.lower()} syntax in {path}") from exc

    if not isinstance(raw_data, dict):
        raise error_type(f"{label} must contain a mapping at the top level: {path}")
    return raw_data


def load_project_mapping() -> tuple[Path, Path, dict[str, object]]:
    from enclosure.shared import layout

    return layout.current_config_mapping()


def section(
    raw_data: object,
    section_path: str,
    model_type: type[ModelT],
    config_path: Path,
) -> ModelT:
    value = raw_data
    for part in _section_parts(section_path):
        if not isinstance(value, dict) or part not in value:
            raise ConfigError(
                f"Missing config section in {config_path}: {section_path}"
            )
        value = value[part]

    if not isinstance(value, dict):
        raise ConfigError(
            f"Invalid config values in {config_path}: {section_path} must be a mapping"
        )

    try:
        return model_type.model_validate(value)
    except ValidationError as exc:
        raise ConfigError(
            f"Invalid config values in {config_path}: {section_path}: {exc}"
        ) from exc


def _section_parts(section_path: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for part in section_path.split(".") if part.strip())
    if not parts:
        raise ConfigError("Config section path must not be empty")
    return parts
