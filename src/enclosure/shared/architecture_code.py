from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modwire import CodeMap, extract_code

from enclosure.shared import architecture_code_cache, config


@dataclass(frozen=True)
class ArchitectureCodeMap:
    project_root: Path
    config_path: Path
    config: object
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
    from enclosure.features.architecture.config import domain

    project_root, config_path, raw_data = config.load_project_mapping()
    architecture_config = domain.ArchitectureConfig.validate_mapping(
        raw_data,
        config_path,
    )
    return ArchitectureCodeMap(
        project_root=project_root,
        config_path=config_path,
        config=architecture_config,
        code_map=architecture_code_cache.extract_with_cache(
            language=architecture_config.language,
            project_root=project_root,
            exclusions=tuple(architecture_config.exclusions),
            extract_code=extract_code,
        ),
    )


__all__ = [
    "ArchitectureCodeMap",
    "extract_architecture_code",
]
