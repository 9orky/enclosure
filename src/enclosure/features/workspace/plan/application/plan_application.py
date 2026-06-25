from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from eventsourcing import application, persistence

from .. import domain


class PlanApplication(application.Application[UUID]):
    def create_plan(self, title: str) -> domain.Plan:
        registry = self._get_or_create_registry()
        plan = domain.Plan(
            title=title.strip(),
            current_stage=domain.PlanState.DRAFT.value,
            source_use_case_id="manual",
            source_plan_item_id="manual",
            created_by_command="workspace plan start",
            schema_version=1,
        )
        registry.activate_plan(domain.PlanId(plan.id))
        try:
            self.save(registry, plan)
        except persistence.IntegrityError as error:
            raise ValueError("Only one active plan may exist") from error
        return self.get_plan(domain.PlanId(plan.id))

    def get_plan(self, plan_id: domain.PlanId) -> domain.Plan:
        return self.repository.get(plan_id.value)

    def get_active_plan(self) -> domain.Plan:
        return self.get_plan(self.active_plan_id())

    def active_plan_id(self) -> domain.PlanId:
        return self.get_registry().active_plan_id()

    def get_registry(self) -> domain.PlanRegistry:
        try:
            return self.repository.get(domain.PLAN_REGISTRY_ID)
        except application.AggregateNotFoundError as error:
            try:
                return self._create_registry_from_legacy_events()
            except LookupError:
                pass
            raise LookupError("No active plan exists") from error

    def release_active_plan(self, plan: domain.Plan, reason: str) -> domain.Plan:
        registry = self.get_registry()
        registry.release_plan(domain.PlanId(plan.id), reason)
        self.save(registry, plan)
        return self.get_plan(domain.PlanId(plan.id))

    def _get_or_create_registry(self) -> domain.PlanRegistry:
        try:
            return self.repository.get(domain.PLAN_REGISTRY_ID)
        except application.AggregateNotFoundError:
            try:
                return self._create_registry_from_legacy_events()
            except LookupError:
                return domain.PlanRegistry(id=domain.PLAN_REGISTRY_ID)

    def _create_registry_from_legacy_events(self) -> domain.PlanRegistry:
        registry = domain.PlanRegistry(id=domain.PLAN_REGISTRY_ID)
        registry.activate_plan(self._legacy_active_plan_id())
        try:
            self.save(registry)
        except persistence.IntegrityError:
            return self.repository.get(domain.PLAN_REGISTRY_ID)
        return self.get_registry()

    def _legacy_active_plan_id(self) -> domain.PlanId:
        active_plan_id: UUID | None = None
        for event in self._legacy_ordered_events():
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

    def _legacy_ordered_events(self) -> Iterable[domain.DomainEvent]:
        start = 1
        limit = self.log_section_size
        while True:
            notifications = self.notification_log.select(start=start, limit=limit)
            if not notifications:
                return
            for notification in notifications:
                yield self.mapper.to_domain_event(notification)
            start = notifications[-1].id + 1


__all__ = ["PlanApplication"]
