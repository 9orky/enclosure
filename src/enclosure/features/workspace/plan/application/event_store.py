from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from eventsourcing.application import Application

from .. import domain


class PlanEventStore(Application[UUID]):
    def create_plan(self, title: str) -> domain.Plan:
        self._reject_when_active_plan_exists()
        plan = domain.Plan(
            title=title.strip(),
            current_stage=domain.PlanState.DRAFT.value,
            source_use_case_id="manual",
            source_plan_item_id="manual",
            created_by_command="workspace plan start",
            schema_version=1,
        )
        self.save(plan)
        return self.get_plan(domain.PlanId(plan.id))

    def get_plan(self, plan_id: domain.PlanId) -> domain.Plan:
        return self.repository.get(plan_id.value)

    def get_active_plan(self) -> domain.Plan:
        return self.get_plan(self.active_plan_id())

    def active_plan_id(self) -> domain.PlanId:
        active_plan_id: UUID | None = None
        for event in self.ordered_events():
            if isinstance(event, domain.Plan.Created):
                active_plan_id = event.originator_id
            if isinstance(event, domain.Plan.StageAdvanced):
                if event.state == domain.PlanState.COMPLETE.value:
                    active_plan_id = None
            if isinstance(event, domain.Plan.Closed):
                active_plan_id = None
        if active_plan_id is None:
            raise LookupError("No active plan exists")
        return domain.PlanId(active_plan_id)

    def ordered_events(self) -> Iterable[domain.DomainEvent]:
        start = 1
        limit = self.log_section_size
        while True:
            notifications = self.notification_log.select(start=start, limit=limit)
            if not notifications:
                return
            for notification in notifications:
                yield self.mapper.to_domain_event(notification)
            start = notifications[-1].id + 1

    def _reject_when_active_plan_exists(self) -> None:
        try:
            self.active_plan_id()
        except LookupError:
            return
        raise ValueError("Only one active plan may exist")


__all__ = ["PlanEventStore"]
