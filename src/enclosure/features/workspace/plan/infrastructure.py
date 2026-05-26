from __future__ import annotations

from . import domain


class FilePlanMaterializer:
    def materialize(
        self,
        document: domain.PlanDocument,
        *,
        force: bool,
    ) -> domain.PlanWriteResult:
        document.plans_root.mkdir(parents=True, exist_ok=True)

        if document.target_path.exists() and not force:
            return domain.PlanWriteResult(document=document, preserved=True)

        overwritten = document.target_path.exists()
        document.target_path.write_text(document.content, encoding="utf-8")
        return domain.PlanWriteResult(
            document=document,
            created=not overwritten,
            overwritten=overwritten,
        )


file_plan_materializer = FilePlanMaterializer()


__all__ = [
    "FilePlanMaterializer",
    "file_plan_materializer",
]
