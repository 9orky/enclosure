from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from . import errors, manifest, metadata, query, root


class SettingsFacade:
    def __init__(self, config_manifest: manifest.Manifest) -> None:
        self._manifest = config_manifest
        self._settings = self._validate_manifest()
        self._metadata = config_manifest._metadata

    @property
    def metadata(self) -> metadata.ConfigMetadata:
        return self._metadata

    def query(self, path: str) -> object:
        return query.ManifestQuery(self._settings).select(path)

    def architecture_root(self) -> Path:
        architecture = self.query("architecture")
        configured_root = getattr(architecture, "architecture_root", "")
        if not configured_root:
            return self.metadata.project_root

        root_path = Path(str(configured_root)).expanduser()
        if not root_path.is_absolute():
            root_path = self.metadata.project_root / root_path
        return root_path.resolve(strict=False)

    def dump_manifest(self) -> str:
        return self._dump_validated_graph()

    def _validate_manifest(self) -> root.EnclosureSettings:
        try:
            return root.EnclosureSettings.model_validate(self._manifest._raw_data)
        except ValidationError as exc:
            raise errors.ConfigError(
                f"Invalid config values in {self._manifest._selected_path}: {exc}"
            ) from exc

    def _dump_validated_graph(self) -> str:
        data = self._settings.model_dump(mode="json", by_alias=True)
        return yaml.safe_dump(data, sort_keys=False)


__all__ = ["SettingsFacade"]
