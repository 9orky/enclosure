from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modwire import (
    CodeMap,
    ExtractionCache,
    SourceRoots,
    extract_code,
    supported_languages,
)

from .config import settings
from .config.errors import ConfigError


@dataclass(frozen=True)
class ArchitectureCodeMap:
    project_root: Path
    config_path: Path
    config: object
    matching_config: object
    code_map: CodeMap

    def report_fields(self) -> dict[str, object]:
        summary = self.code_map.extraction_result.summary
        language = getattr(self.config, "language")
        return {
            "project_root": self.project_root,
            "config_path": self.config_path,
            "config_format": self.config_path.suffix.lstrip("."),
            "language": language,
            "runtime_command": self.code_map.runtime_command,
            "files_found": summary.files_found,
            "files_excluded": summary.files_excluded,
            "files_checked": summary.files_checked,
        }


def extract_architecture_code() -> ArchitectureCodeMap:
    project_root = settings.metadata.project_root
    config_path = settings.metadata.canonical_config_path
    architecture_config = settings.query("architecture")
    _validate_supported_language(architecture_config)
    architecture_root = settings.architecture_root()
    code_map = extract_code(
        language=architecture_config.language,
        sources_root=architecture_root,
        exclusions=_extraction_exclusions(architecture_config),
        source_roots=SourceRoots(workspace_root=project_root),
        cache=ExtractionCache(
            root=settings.metadata.cache_dir / "modwire",
            max_entries=3,
        ),
    )
    return ArchitectureCodeMap(
        project_root=project_root,
        config_path=config_path,
        config=architecture_config,
        matching_config=_matching_config(architecture_config),
        code_map=code_map,
    )


def _extraction_exclusions(architecture_config: object) -> tuple[str, ...]:
    return tuple(getattr(architecture_config, "exclusions", ()) or ())


class _ArchitectureMatchingConfig:
    def __init__(self, architecture_config: object) -> None:
        self._architecture_config = architecture_config

    @property
    def architecture_root(self) -> str:
        return ""

    def __getattr__(self, name: str) -> object:
        return getattr(self._architecture_config, name)


def _matching_config(architecture_config: object) -> object:
    if not getattr(architecture_config, "architecture_root", ""):
        return architecture_config
    return _ArchitectureMatchingConfig(architecture_config)


def _validate_supported_language(architecture_config: object) -> None:
    language = getattr(architecture_config, "language", "")
    if language not in supported_languages():
        raise ConfigError(f"unsupported language: {language}")


__all__ = [
    "ArchitectureCodeMap",
    "extract_architecture_code",
]
