import attrs
from sqlalchemy.engine.base import Engine

from src.adapters.db import engine
from src.domain.models import InSyncSlackChannelItem, SlackEvent, Tenant

from .entities import InSyncSlackChannelDBEntity, SlackEventDBEntity, TenantDBEntity
from .respositories import (
    InSyncChannelRepository,
    SlackEventRepository,
    TenantRepository,
)


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

    async def get_by_id(self, tenant_id: str) -> Tenant:
        async with self.engine.begin() as conn:
            tenant_entity = await TenantRepository(conn).get_by_id(tenant_id)
            result = self._map_to_domain(tenant_entity)
        return result


class InSyncChannelDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(
        self, insync_slack_channel: InSyncSlackChannelItem
    ) -> InSyncSlackChannelDBEntity:
        return InSyncSlackChannelDBEntity(
            tenant_id=insync_slack_channel.tenant_id,
            context_team_id=insync_slack_channel.context_team_id,
            created=insync_slack_channel.created,
            creator=insync_slack_channel.creator,
            id=insync_slack_channel.id,
            is_archived=insync_slack_channel.is_archived,
            is_channel=insync_slack_channel.is_channel,
            is_ext_shared=insync_slack_channel.is_ext_shared,
            is_general=insync_slack_channel.is_general,
            is_group=insync_slack_channel.is_group,
            is_im=insync_slack_channel.is_im,
            is_member=insync_slack_channel.is_member,
            is_mpim=insync_slack_channel.is_mpim,
            is_org_shared=insync_slack_channel.is_org_shared,
            is_pending_ext_shared=insync_slack_channel.is_pending_ext_shared,
            is_private=insync_slack_channel.is_private,
            is_shared=insync_slack_channel.is_shared,
            name=insync_slack_channel.name,
            name_normalized=insync_slack_channel.name_normalized,
            num_members=insync_slack_channel.num_members,
            parent_conversation=insync_slack_channel.parent_conversation,
            pending_connected_team_ids=insync_slack_channel.pending_connected_team_ids,
            pending_shared=insync_slack_channel.pending_shared,
            previous_names=insync_slack_channel.previous_names,
            purpose=insync_slack_channel.purpose,
            shared_team_ids=insync_slack_channel.shared_team_ids,
            topic=insync_slack_channel.topic,
            unlinked=insync_slack_channel.unlinked,
            updated=insync_slack_channel.updated,
            updated_at=insync_slack_channel.updated_at,
            created_at=insync_slack_channel.created_at,
        )

    def _map_to_domain(self, sync_channel_entity: InSyncSlackChannelDBEntity):
        return InSyncSlackChannelItem(
            tenant_id=sync_channel_entity.tenant_id,
            context_team_id=sync_channel_entity.context_team_id,
            created=sync_channel_entity.created,
            creator=sync_channel_entity.creator,
            id=sync_channel_entity.id,
            is_archived=sync_channel_entity.is_archived,
            is_channel=sync_channel_entity.is_channel,
            is_ext_shared=sync_channel_entity.is_ext_shared,
            is_general=sync_channel_entity.is_general,
            is_group=sync_channel_entity.is_group,
            is_im=sync_channel_entity.is_im,
            is_member=sync_channel_entity.is_member,
            is_mpim=sync_channel_entity.is_mpim,
            is_org_shared=sync_channel_entity.is_org_shared,
            is_pending_ext_shared=sync_channel_entity.is_pending_ext_shared,
            is_private=sync_channel_entity.is_private,
            is_shared=sync_channel_entity.is_shared,
            name=sync_channel_entity.name,
            name_normalized=sync_channel_entity.name_normalized,
            num_members=sync_channel_entity.num_members,
            parent_conversation=sync_channel_entity.parent_conversation,
            pending_connected_team_ids=sync_channel_entity.pending_connected_team_ids,
            pending_shared=sync_channel_entity.pending_shared,
            previous_names=sync_channel_entity.previous_names,
            purpose=sync_channel_entity.purpose,
            shared_team_ids=sync_channel_entity.shared_team_ids,
            topic=sync_channel_entity.topic,
            unlinked=sync_channel_entity.unlinked,
            updated=sync_channel_entity.updated,
            updated_at=sync_channel_entity.updated_at,
            created_at=sync_channel_entity.created_at,
        )

    async def save(self, insync_slack_channel: InSyncSlackChannelItem):
        db_entity = self._map_to_db_entity(insync_slack_channel)
        async with self.engine.begin() as conn:
            sync_channel_entity = await InSyncChannelRepository(conn).save(db_entity)
            result = self._map_to_domain(sync_channel_entity)
        return result
