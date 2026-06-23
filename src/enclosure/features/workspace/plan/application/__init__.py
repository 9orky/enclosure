from __future__ import annotations

from . import commands, queries

create_plan_document = commands.create_plan_document
describe_plan_document = queries.describe_plan_document

__all__ = [
    "create_plan_document",
    "describe_plan_document",
]
