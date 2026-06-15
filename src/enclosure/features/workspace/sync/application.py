from __future__ import annotations

from enclosure.shared import layout

from . import domain, infrastructure


def bootstrap_project() -> domain.BootstrapProjectResult:
    return infrastructure.write_plan_materializer.materialize(_workspace().plan_bootstrap())


def update_project() -> domain.UpdateProjectResult:
    return infrastructure.write_plan_materializer.materialize(_workspace().plan_update())


def migrate_project() -> domain.MigrateProjectResult:
    migration_plan = _workspace().plan_migrate()
    result = infrastructure.write_plan_materializer.materialize(
        migration_plan.write_plan,
    )
    return {
        **result,
        "config_warnings": migration_plan.config_warnings,
    }


def describe_workspace_contract() -> domain.WorkspaceContractSummary:
    return _workspace().summarize()


def _workspace() -> domain.Workspace:
    return infrastructure.file_repository.load(layout.current_project_root())
