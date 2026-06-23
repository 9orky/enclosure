from __future__ import annotations

from .. import domain, infrastructure
from . import queries


def create_plan_document(name: str, *, force: bool) -> domain.PlanWriteResult:
    return infrastructure.file_plan_materializer.materialize(
        queries.describe_plan_document(name),
        force=force,
    )


__all__ = ["create_plan_document"]
