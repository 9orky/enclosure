from __future__ import annotations

import yaml
from pydantic import ValidationError

from .errors import ConfigError
from .manifest import Manifest
from .metadata import ConfigMetadata
from .query import ManifestQuery
from .root import EnclosureSettings


class SettingsFacade:
    def __init__(self, manifest: Manifest) -> None:
        self._manifest = manifest
        self._settings = self._validate_manifest()
        self._metadata = manifest._metadata

    @property
    def metadata(self) -> ConfigMetadata:
        return self._metadata

    def query(self, path: str) -> object:
        return ManifestQuery(self._settings).select(path)

    def dump_manifest(self) -> str:
        return self._dump_validated_graph()

    def _validate_manifest(self) -> EnclosureSettings:
        try:
            return EnclosureSettings.model_validate(self._manifest._raw_data)
        except ValidationError as exc:
            raise ConfigError(
                f"Invalid config values in {self._manifest._selected_path}: {exc}"
            ) from exc

    def _dump_validated_graph(self) -> str:
        data = self._settings.model_dump(mode="json", by_alias=True)
        return yaml.safe_dump(data, sort_keys=False)


__all__ = ["SettingsFacade"]
