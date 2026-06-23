from __future__ import annotations

from .. import domain, infrastructure
from . import queries


def bootstrap_project(*, source_kind: str) -> domain.BootstrapProjectResult:
    return infrastructure.write_plan_materializer.materialize(
        queries.load_workspace_contract(source_kind).plan_bootstrap()
    )


def update_project() -> domain.UpdateProjectResult:
    return infrastructure.write_plan_materializer.materialize(
        queries.load_workspace_contract("").plan_update()
    )


def migrate_project() -> domain.MigrateProjectResult:
    migration_plan = queries.load_workspace_contract("").plan_migrate()
    result = infrastructure.write_plan_materializer.materialize(
        migration_plan.write_plan,
    )
    return {
        **result,
        "config_warnings": migration_plan.config_warnings,
    }


__all__ = [
    "bootstrap_project",
    "migrate_project",
    "update_project",
]
