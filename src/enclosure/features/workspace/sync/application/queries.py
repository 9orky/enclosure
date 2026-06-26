from __future__ import annotations

from pathlib import Path

from enclosure.shared.config import manifest, metadata, settings

from .. import domain, infrastructure


def describe_workspace_contract() -> domain.WorkspaceContractSummary:
    return load_workspace_contract("").summarize()


def load_bootstrap_workspace_contract(source_kind: str) -> domain.Workspace:
    return infrastructure.file_repository.load(
        metadata.ConfigMetadata(project_root=Path.cwd()),
        default_config_content=manifest.Manifest.dump_default(),
        source_kind=source_kind,
    )


def load_workspace_contract(source_kind: str) -> domain.Workspace:
    return infrastructure.file_repository.load(
        settings.metadata,
        default_config_content=settings.dump_manifest(),
        source_kind=source_kind,
    )


__all__ = [
    "describe_workspace_contract",
    "load_bootstrap_workspace_contract",
    "load_workspace_contract",
]
