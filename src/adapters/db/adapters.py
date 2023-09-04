import attrs
from sqlalchemy.engine.base import Engine

from src.adapters.db import engine
from src.domain.models import SlackEvent, Tenant

from .entities import SlackEventDBEntity, TenantDBEntity
from .respositories import SlackEventRepository, TenantRepository


class SlackEventDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(self, slack_event: SlackEvent) -> SlackEventDBEntity:
        event = attrs.asdict(slack_event.event) if slack_event.event else None
        return SlackEventDBEntity(
            event_id=slack_event.event_id,
            tenant_id=slack_event.tenant_id,
            slack_event_ref=slack_event.slack_event_ref,
            inner_event_type=slack_event.inner_event_type,
            event=event,
            event_ts=slack_event.event_ts,
            api_app_id=slack_event.api_app_id,
            token=slack_event.token,
            payload=slack_event.payload,
            is_ack=slack_event.is_ack,
        )

    def _map_to_domain(self, slack_event_entity: SlackEventDBEntity) -> SlackEvent:
        tenant_id = slack_event_entity.tenant_id
        payload = slack_event_entity.payload
        slack_event = SlackEvent.init_from_payload(tenant_id=tenant_id, payload=payload)
        return slack_event

    async def save(self, slack_event: SlackEvent) -> SlackEvent:
        db_entity = self._map_to_db_entity(slack_event)
        async with self.engine.begin() as conn:
            slack_event_entity = await SlackEventRepository(conn).save(db_entity)
            result = self._map_to_domain(slack_event_entity)
        return result

    async def find_by_slack_event_ref(self, slack_event_ref: str) -> SlackEvent | None:
        async with self.engine.begin() as conn:
            slack_event_entity = await SlackEventRepository(
                conn
            ).find_by_slack_event_ref(slack_event_ref)
            if slack_event_entity is None:
                return None
            else:
                result = self._map_to_domain(slack_event_entity)
        return result


class TenantDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(self, tenant: Tenant) -> TenantDBEntity:
        return TenantDBEntity(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            slack_team_ref=tenant.slack_team_ref,
        )

    def _map_to_domain(self, tenant_entity: TenantDBEntity) -> Tenant:
        tenant = Tenant(tenant_id=tenant_entity.tenant_id, name=tenant_entity.name)
        tenant.set_slack_team_ref(tenant_entity.slack_team_ref)
        return tenant

    async def save(self, tenant: Tenant) -> Tenant:
        db_entity = self._map_to_db_entity(tenant)
        async with self.engine.begin() as conn:
            tenant_entity = await TenantRepository(conn).save(db_entity)
            result = self._map_to_domain(tenant_entity)
        return result

    async def find_by_id(self, tenant_id: str) -> Tenant | None:
        async with self.engine.begin() as conn:
            tenant_entity = await TenantRepository(conn).find_by_id(tenant_id)
            if tenant_entity is None:
                return None
            else:
                result = self._map_to_domain(tenant_entity)
        return result

    async def find_by_slack_team_ref(self, slack_team_ref: str) -> Tenant | None:
        async with self.engine.begin() as conn:
            tenant_entity = await TenantRepository(conn).find_by_slack_team_ref(
                slack_team_ref
            )
            if tenant_entity is None:
                return None
            else:
                result = self._map_to_domain(tenant_entity)
        return result
