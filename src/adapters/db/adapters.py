from sqlalchemy.engine.base import Engine

from src.adapters.db import engine
from src.domain.models import (
    InSyncSlackChannel,
    InSyncSlackUser,
    Issue,
    LinkedSlackChannel,
    SlackEvent,
    Tenant,
    TriageSlackChannel,
)

from .entities import (
    InSyncSlackChannelDBEntity,
    InSyncSlackUserDBEntity,
    IssueDBEntity,
    LinkedSlackChannelDBEntity,
    SlackEventDBEntity,
    TenantDBEntity,
)
from .respositories import (
    InSyncChannelRepository,
    IssueRepository,
    LinkedSlackChannelRepository,
    SlackEventRepository,
    TenantRepository,
)


class SlackEventDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(self, slack_event: SlackEvent) -> SlackEventDBEntity:
        event = slack_event.event.to_dict() if slack_event.event else None
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
        slack_event = SlackEvent.from_payload(
            tenant_id=tenant_id, event_id=slack_event_entity.event_id, payload=payload
        )
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
        tenant = Tenant(
            tenant_id=tenant_entity.tenant_id,
            name=tenant_entity.name,
            slack_team_ref=tenant_entity.slack_team_ref,
        )
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
        self, insync_slack_channel: InSyncSlackChannel
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

    def _map_to_domain(
        self, sync_channel_entity: InSyncSlackChannelDBEntity
    ) -> InSyncSlackChannel:
        return InSyncSlackChannel(
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

    async def save(
        self, insync_slack_channel: InSyncSlackChannel
    ) -> InSyncSlackChannel:
        db_entity = self._map_to_db_entity(insync_slack_channel)
        async with self.engine.begin() as conn:
            sync_channel_entity = await InSyncChannelRepository(conn).save(db_entity)
            result = self._map_to_domain(sync_channel_entity)
        return result

    async def get_by_tenant_id_slack_channel_ref(
        self, tenant_id: str, slack_channel_ref: str
    ) -> InSyncSlackChannel:
        async with self.engine.begin() as conn:
            insync_channel_entity = await InSyncChannelRepository(
                conn
            ).get_by_tenant_id_id(tenant_id, slack_channel_ref)
            result = self._map_to_domain(insync_channel_entity)
        return result


class LinkedSlackChannelDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(
        self, linked_slack_channel: LinkedSlackChannel
    ) -> LinkedSlackChannelDBEntity:
        triage_channel = linked_slack_channel.triage_channel
        return LinkedSlackChannelDBEntity(
            tenant_id=linked_slack_channel.tenant_id,
            linked_slack_channel_id=linked_slack_channel.linked_slack_channel_id,
            slack_channel_ref=linked_slack_channel.slack_channel_ref,
            slack_channel_name=linked_slack_channel.slack_channel_name,
            triage_slack_channel_ref=triage_channel.slack_channel_ref,
            triage_slack_channel_name=triage_channel.slack_channel_name,
        )

    def _map_to_domain(
        self, linked_slack_channel_entity: LinkedSlackChannelDBEntity
    ) -> LinkedSlackChannel:
        linked_channel = LinkedSlackChannel(
            tenant_id=linked_slack_channel_entity.tenant_id,
            linked_slack_channel_id=linked_slack_channel_entity.linked_slack_channel_id,
            slack_channel_ref=linked_slack_channel_entity.slack_channel_ref,
            slack_channel_name=linked_slack_channel_entity.slack_channel_name,
        )
        linked_channel.add_triage_channel(
            TriageSlackChannel(
                tenant_id=linked_slack_channel_entity.tenant_id,
                slack_channel_ref=linked_slack_channel_entity.triage_slack_channel_ref,
                slack_channel_name=linked_slack_channel_entity.triage_slack_channel_name,
            )
        )
        return linked_channel

    async def save(self, linked_channel: LinkedSlackChannel) -> LinkedSlackChannel:
        db_entity = self._map_to_db_entity(linked_channel)
        async with self.engine.begin() as conn:
            linked_channel_entity = await LinkedSlackChannelRepository(conn).save(
                db_entity
            )
            result = self._map_to_domain(linked_channel_entity)
        return result

    async def find_by_id(
        self, linked_slack_channel_id: str
    ) -> LinkedSlackChannel | None:
        async with self.engine.begin() as conn:
            linked_channel_entity = await LinkedSlackChannelRepository(
                conn
            ).find_by_linked_slack_channel_id(linked_slack_channel_id)
            if linked_channel_entity is None:
                return None
            result = self._map_to_domain(linked_channel_entity)
        return result

    async def get_by_id(self, linked_slack_channel_id: str) -> LinkedSlackChannel:
        async with self.engine.begin() as conn:
            linked_channel_entity = await LinkedSlackChannelRepository(
                conn
            ).get_by_linked_slack_channel_id(linked_slack_channel_id)
            result = self._map_to_domain(linked_channel_entity)
        return result

    async def find_by_slack_channel_ref(
        self, slack_channel_ref: str
    ) -> LinkedSlackChannel | None:
        async with self.engine.begin() as conn:
            linked_channel_entity = await LinkedSlackChannelRepository(
                conn
            ).find_by_slack_channel_ref(slack_channel_ref)
            if linked_channel_entity is None:
                return None
            result = self._map_to_domain(linked_channel_entity)
        return result

    async def find_by_tenant_id_slack_channel_name(
        self, tenant_id: str, slack_channel_name: str
    ) -> LinkedSlackChannel | None:
        async with self.engine.begin() as conn:
            linked_channel_entity = await LinkedSlackChannelRepository(
                conn
            ).find_by_tenant_id_slack_channel_name(tenant_id, slack_channel_name)
            if linked_channel_entity is None:
                return None
            result = self._map_to_domain(linked_channel_entity)
        return result


class IssueDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(self, issue: Issue) -> IssueDBEntity:
        return IssueDBEntity(
            tenant_id=issue.tenant_id,
            issue_id=issue.issue_id,
            issue_number=issue.issue_number,
            body=issue.body,
            status=issue.status,
            priority=issue.priority,
            tags=issue.tags,
            linked_slack_channel_id=issue.linked_slack_channel_id,
        )

    def _map_to_domain(self, issue_entity: IssueDBEntity) -> Issue:
        issue = Issue(
            tenant_id=issue_entity.tenant_id,
            issue_id=issue_entity.issue_id,
            issue_number=issue_entity.issue_number,
            body=issue_entity.body,
            status=issue_entity.status,
            priority=issue_entity.priority,
        )
        issue.tags = issue_entity.tags
        issue.linked_slack_channel_id = issue_entity.linked_slack_channel_id
        return issue

    async def save(self, issue: Issue) -> Issue:
        db_entity = self._map_to_db_entity(issue)
        async with self.engine.begin() as conn:
            issue_entity = await IssueRepository(conn).save(db_entity)
            result = self._map_to_domain(issue_entity)
        return result


class InSyncSlackUserDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(
        self, insync_slack_user: InSyncSlackUser
    ) -> InSyncSlackUserDBEntity:
        return InSyncSlackUserDBEntity(
            tenant_id=insync_slack_user.tenant_id,
            id=insync_slack_user.id,
            is_admin=insync_slack_user.is_admin,
            is_app_user=insync_slack_user.is_app_user,
            is_bot=insync_slack_user.is_bot,
            is_email_confirmed=insync_slack_user.is_email_confirmed,
            is_owner=insync_slack_user.is_owner,
            is_primary_owner=insync_slack_user.is_primary_owner,
            is_restricted=insync_slack_user.is_restricted,
            is_stranger=insync_slack_user.is_stranger,
            is_ultra_restricted=insync_slack_user.is_ultra_restricted,
            name=insync_slack_user.name,
            profile=insync_slack_user.profile,
            real_name=insync_slack_user.real_name,
            team_id=insync_slack_user.team_id,
            tz=insync_slack_user.tz,
            tz_label=insync_slack_user.tz_label,
            tz_offset=insync_slack_user.tz_offset,
            updated=insync_slack_user.updated,
        )

    def _map_to_domain(
        self, insync_slack_user_entity: InSyncSlackUserDBEntity
    ) -> InSyncSlackUser:
        return InSyncSlackUser(
            tenant_id=insync_slack_user_entity.tenant_id,
            id=insync_slack_user_entity.id,
            is_admin=insync_slack_user_entity.is_admin,
            is_app_user=insync_slack_user_entity.is_app_user,
            is_bot=insync_slack_user_entity.is_bot,
            is_email_confirmed=insync_slack_user_entity.is_email_confirmed,
            is_owner=insync_slack_user_entity.is_owner,
            is_primary_owner=insync_slack_user_entity.is_primary_owner,
            is_restricted=insync_slack_user_entity.is_restricted,
            is_stranger=insync_slack_user_entity.is_stranger,
            is_ultra_restricted=insync_slack_user_entity.is_ultra_restricted,
            name=insync_slack_user_entity.name,
            profile=insync_slack_user_entity.profile,
            real_name=insync_slack_user_entity.real_name,
            team_id=insync_slack_user_entity.team_id,
            tz=insync_slack_user_entity.tz,
            tz_label=insync_slack_user_entity.tz_label,
            tz_offset=insync_slack_user_entity.tz_offset,
            updated=insync_slack_user_entity.updated,
        )

    async def save(self, insync_slack_user: InSyncSlackUser) -> InSyncSlackUser:
        db_entity = self._map_to_db_entity(insync_slack_user)
        async with self.engine.begin() as conn:
            insync_slack_user_entity = await InSyncChannelRepository(conn).save(
                db_entity
            )
            result = self._map_to_domain(insync_slack_user_entity)
        return result