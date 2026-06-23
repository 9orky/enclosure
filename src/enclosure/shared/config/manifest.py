from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import errors, metadata, root


class Manifest:
    _MANIFEST_FILE_NAMES = ("enclosure.yaml", "enclosure.yml")

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root.expanduser().resolve()
        self._target_dir = self._project_root / ".enclosure"
        self._selected_path = self._find_config_path()
        self._metadata = metadata.ConfigMetadata(project_root=self._project_root)
        self._raw_data = self._load_yaml_mapping(self._selected_path)

    @staticmethod
    def dump_default() -> str:
        data = root.EnclosureSettings().model_dump(mode="json", by_alias=True)
        return yaml.safe_dump(data, sort_keys=False)

    def _find_config_path(self) -> Path:
        for file_name in self._MANIFEST_FILE_NAMES:
            candidate = self._target_dir / file_name
            if candidate.is_file():
                return candidate

        searched = ", ".join(
            str(self._target_dir / file_name)
            for file_name in self._MANIFEST_FILE_NAMES
        )
        raise errors.ConfigError(f"Could not find a configuration file. Looked for {searched}.")

    def _load_yaml_mapping(self, path: Path) -> dict[str, Any]:
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise errors.ConfigError(f"Could not read config file: {path}") from exc

        try:
            raw_data = yaml.safe_load(raw_text) or {}
        except yaml.YAMLError as exc:
            raise errors.ConfigError(f"Invalid config file syntax in {path}") from exc

        if not isinstance(raw_data, dict):
            raise errors.ConfigError(f"Config file must contain a mapping at the top level: {path}")
        return raw_data

__all__ = [
    "Manifest",
]
