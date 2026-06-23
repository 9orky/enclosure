from __future__ import annotations

from . import commands, queries

bootstrap_project = commands.bootstrap_project
describe_workspace_contract = queries.describe_workspace_contract
migrate_project = commands.migrate_project
update_project = commands.update_project

__all__ = [
    "bootstrap_project",
    "describe_workspace_contract",
    "migrate_project",
    "update_project",
]
