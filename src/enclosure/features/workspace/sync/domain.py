from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

from enclosure.shared import config, layout


class SyncConfig(config.StrictConfigModel):
    pass


@dataclass(frozen=True)
class SharedRulePath:
    value: Path

    def __post_init__(self) -> None:
        normalized_value = Path(self.value)
        forbidden_parts = {"..", "."}
        if (
            normalized_value.is_absolute()
            or not normalized_value.parts
            or normalized_value.parts[0] in {"rules", "overrides"}
            or any(part in forbidden_parts for part in normalized_value.parts)
        ):
            raise ValueError("Shared rule paths must stay inside the shared rules root")
        object.__setattr__(self, "value", normalized_value)


@dataclass(frozen=True)
class SharedRuleDocument:
    shared_rule_path: SharedRulePath
    content: str


class SyncAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"


@dataclass(frozen=True)
class SyncChange:
    target_path: Path
    action: SyncAction
    content: str


@dataclass(frozen=True)
class WorkspaceContractSummary:
    project_root: Path
    target_dir: Path
    config_path: Path
    enclosure_dir_exists: bool
    config_exists: bool
    shared_rule_paths: tuple[Path, ...] = ()
    missing_shared_rule_paths: tuple[Path, ...] = ()
    local_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class WorkspaceWritePlan:
    target_dir: Path
    required_dirs: tuple[Path, ...] = ()
    changes: tuple[SyncChange, ...] = ()
    preserved_paths: tuple[Path, ...] = ()


class ProjectSyncResult(TypedDict):
    target_dir: Path
    created_dir: bool
    created_files: tuple[Path, ...]
    updated_files: tuple[Path, ...]
    preserved_files: tuple[Path, ...]


BootstrapProjectResult = ProjectSyncResult
UpdateProjectResult = ProjectSyncResult


@dataclass(frozen=True)
class Workspace:
    project_root: Path
    shared_rule_documents: tuple[SharedRuleDocument, ...]
    config_content: str
    bootstrap_instruction_content: str
    agent_instruction_content: str
    existing_shared_rule_paths: tuple[Path, ...] = ()
    local_paths: tuple[Path, ...] = ()
    enclosure_dir_exists: bool = False
    config_exists: bool = False
    bootstrap_instruction_exists: bool = False
    agent_instruction_exists: bool = False
    layout: layout.EnclosureProjectLayout = layout.EnclosureProjectLayout()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "shared_rule_documents",
            tuple(
                sorted(
                    self.shared_rule_documents,
                    key=lambda document: document.shared_rule_path.value.as_posix(),
                )
            ),
        )
        object.__setattr__(
            self,
            "existing_shared_rule_paths",
            _unique_paths(tuple(self.existing_shared_rule_paths)),
        )
        object.__setattr__(
            self,
            "local_paths",
            _unique_paths(tuple(self.local_paths)),
        )

    def expected_shared_rule_paths(self) -> tuple[Path, ...]:
        rules_dir = self.layout.rules_dir(self.project_root)
        return tuple(
            rules_dir / document.shared_rule_path.value
            for document in self.shared_rule_documents
        )

    def plan_bootstrap(self) -> WorkspaceWritePlan:
        return self._build_write_plan(
            overwrite_shared_rule_documents=False,
            overwrite_bootstrap_instruction=False,
        )

    def plan_update(self) -> WorkspaceWritePlan:
        return self._build_write_plan(
            overwrite_shared_rule_documents=True,
            overwrite_bootstrap_instruction=True,
        )

    def summarize(self) -> WorkspaceContractSummary:
        expected_shared_rule_paths = self.expected_shared_rule_paths()
        existing_shared_rule_paths = set(self.existing_shared_rule_paths)
        return WorkspaceContractSummary(
            project_root=self.project_root,
            target_dir=self.layout.target_dir(self.project_root),
            config_path=self.layout.config_path(self.project_root, None),
            enclosure_dir_exists=self.enclosure_dir_exists,
            config_exists=self.config_exists,
            shared_rule_paths=tuple(
                path
                for path in expected_shared_rule_paths
                if path in existing_shared_rule_paths
            ),
            missing_shared_rule_paths=tuple(
                path
                for path in expected_shared_rule_paths
                if path not in existing_shared_rule_paths
            ),
            local_paths=self.local_paths,
        )

    def _build_write_plan(
        self,
        *,
        overwrite_shared_rule_documents: bool,
        overwrite_bootstrap_instruction: bool,
    ) -> WorkspaceWritePlan:
        changes: list[SyncChange] = []
        preserved_paths: list[Path] = []

        for target_path, exists, content, overwrite in (
            (
                self.layout.config_path(self.project_root, None),
                self.config_exists,
                self.config_content,
                False,
            ),
            (
                self.layout.bootstrap_instruction_path(self.project_root),
                self.bootstrap_instruction_exists,
                self.bootstrap_instruction_content,
                overwrite_bootstrap_instruction,
            ),
            (
                self.layout.agent_instruction_path(self.project_root),
                self.agent_instruction_exists,
                self.agent_instruction_content,
                overwrite_bootstrap_instruction,
            ),
        ):
            _append_file_plan(
                changes,
                preserved_paths,
                target_path,
                exists,
                content,
                overwrite,
            )

        existing_shared_rule_paths = set(self.existing_shared_rule_paths)
        rules_dir = self.layout.rules_dir(self.project_root)
        for document in self.shared_rule_documents:
            target_path = rules_dir / document.shared_rule_path.value
            _append_file_plan(
                changes,
                preserved_paths,
                target_path,
                target_path in existing_shared_rule_paths,
                document.content,
                overwrite_shared_rule_documents,
            )

        return WorkspaceWritePlan(
            target_dir=self.layout.target_dir(self.project_root),
            required_dirs=_sort_paths(
                (
                    self.layout.recipes_dir(self.project_root),
                    self.layout.local_rules_dir(self.project_root),
                )
            ),
            changes=tuple(changes),
            preserved_paths=_sort_paths(tuple(preserved_paths)),
        )


def _append_file_plan(
    changes: list[SyncChange],
    preserved_paths: list[Path],
    target_path: Path,
    exists: bool,
    content: str,
    overwrite: bool,
) -> None:
    if exists and not overwrite:
        preserved_paths.append(target_path)
        return

    changes.append(
        SyncChange(
            target_path=target_path,
            action=SyncAction.UPDATE if exists else SyncAction.CREATE,
            content=content,
        )
    )


def _unique_paths(values: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(_sort_paths(values)))


def _sort_paths(values: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(sorted(values, key=lambda path: path.as_posix()))
