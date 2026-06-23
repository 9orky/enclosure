from __future__ import annotations

from enclosure.shared.config import settings

from .. import domain, infrastructure


def describe_workspace_contract() -> domain.WorkspaceContractSummary:
    return load_workspace_contract("").summarize()


def load_workspace_contract(source_kind: str) -> domain.Workspace:
    return infrastructure.file_repository.load(
        settings.metadata,
        default_config_content=settings.dump_manifest(),
        source_kind=source_kind,
    )


__all__ = [
    "describe_workspace_contract",
    "load_workspace_contract",
]
