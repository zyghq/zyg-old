import abc
import json
import uuid

from sqlalchemy import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from .entities import (
    InSyncSlackChannelDBEntity,
    InSyncSlackUserDBEntity,
    IssueDBEntity,
    SlackChannelDBEntity,
    SlackEventDBEntity,
    TenantDBEntity,
    UserDBEntity,
)
from .exceptions import DBIntegrityException, DBNotFoundException


class BaseRepository:
    @classmethod
    def generate_id(cls) -> str:
        uuid_object = uuid.uuid4()
        base32 = uuid_object.hex
        return base32


class AbstractTenantRepository(abc.ABC):
    @abc.abstractmethod
    async def find_by_id(self, tenant_id: str) -> TenantDBEntity | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def save(self, tenant: TenantDBEntity) -> TenantDBEntity:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_slack_team_ref(
        self, slack_team_ref: str
    ) -> TenantDBEntity | None:
        raise NotImplementedError


class TenantRepository(AbstractTenantRepository, BaseRepository):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def find_by_slack_team_ref(
        self, slack_team_ref: str
    ) -> TenantDBEntity | None:
        query = """
            select tenant_id, slack_team_ref, name, created_at, updated_at
            from tenant
            where slack_team_ref = :slack_team_ref
        """
        parameters = {"slack_team_ref": slack_team_ref}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return TenantDBEntity(**result)

    async def find_by_id(self, tenant_id: str) -> TenantDBEntity | None:
        query = """
            select tenant_id, slack_team_ref, name, created_at, updated_at
            from tenant
            where tenant_id = :tenant_id
        """
        parameters = {"tenant_id": tenant_id}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return TenantDBEntity(**result)

    async def get_by_id(self, tenant_id: str) -> TenantDBEntity:
        tenant = await self.find_by_id(tenant_id)
        if tenant is None:
            raise DBNotFoundException(f"tenant with id `{tenant_id}` not found")
        return tenant

    async def _upsert(self, tenant: TenantDBEntity) -> TenantDBEntity:
        query = """
            insert into tenant (
                tenant_id,
                name,
                slack_team_ref
            )
            values (
                :tenant_id,
                :name,
                :slack_team_ref
            )
            on conflict (tenant_id) do update set
                name = :name
                slack_team_ref = :slack_team_ref
                updated_at = now()
            returning tenant_id, slack_team_ref name, created_at, updated_at
        """
        parameters = {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "slack_team_ref": tenant.slack_team_ref,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return TenantDBEntity(**result)

    async def _insert(self, tenant: TenantDBEntity) -> TenantDBEntity:
        tenant_id = self.generate_id()
        query = """
            insert into tenant (
                tenant_id,
                name,
                slack_team_ref
            )
            values (
                :tenant_id,
                :name,
                :slack_team_ref
            )
            returning tenant_id, slack_team_ref, name, created_at, updated_at
        """
        parameters = {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "slack_team_ref": tenant.slack_team_ref,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return TenantDBEntity(**result)

    async def save(self, tenant: TenantDBEntity) -> TenantDBEntity:
        if tenant.tenant_id is None:
            return await self._insert(tenant)
        return await self._upsert(tenant)


class AbstractSlackEventRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, slack_event: SlackEventDBEntity):
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(self, event_id: str):
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_slack_event_ref(self, slack_event_ref: str):
        raise NotImplementedError


class SlackEventRepository(AbstractSlackEventRepository, BaseRepository):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def find_by_slack_event_ref(self, slack_event_ref: str):
        query = """
            select event_id, tenant_id, slack_event_ref,
                inner_event_type, event_dispatched_ts, api_app_id,
                token, payload, is_ack, created_at, updated_at
            from slack_event
            where slack_event_ref = :slack_event_ref
        """
        parameters = {"slack_event_ref": slack_event_ref}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return SlackEventDBEntity(**result)

    async def find_by_id(self, event_id: str):
        query = """
            select event_id, tenant_id, slack_event_ref,
                inner_event_type, event_dispatched_ts, api_app_id,
                token, payload, is_ack, created_at, updated_at
            from slack_event
            where event_id = :event_id
        """
        parameters = {"event_id": event_id}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return SlackEventDBEntity(**result)

    async def _upsert(self, slack_event: SlackEventDBEntity) -> SlackEventDBEntity:
        query = """
            insert into slack_event (
                event_id, tenant_id, slack_event_ref,
                inner_event_type, event_dispatched_ts, api_app_id,
                token, payload, is_ack
            )
            values (
                :event_id, :tenant_id, :slack_event_ref,
                :inner_event_type, :event_dispatched_ts, :api_app_id,
                :token, :payload, :is_ack
            )
            on conflict (event_id) do update set
                tenant_id = :tenant_id,
                slack_event_ref = :slack_event_ref,
                inner_event_type = :inner_event_type,
                event_dispatched_ts = :event_dispatched_ts,
                api_app_id = :api_app_id,
                token = :token,
                payload = :payload,
                is_ack = :is_ack,
                updated_at = now()
            returning event_id, tenant_id, slack_event_ref,
                inner_event_type, event_dispatched_ts, api_app_id,
                token, payload, is_ack, created_at, updated_at
        """
        parameters = {
            "event_id": slack_event.event_id,
            "tenant_id": slack_event.tenant_id,
            "slack_event_ref": slack_event.slack_event_ref,
            "inner_event_type": slack_event.inner_event_type,
            "event_dispatched_ts": slack_event.event_dispatched_ts,
            "api_app_id": slack_event.api_app_id,
            "token": slack_event.token,
            "payload": json.dumps(slack_event.payload)
            if isinstance(slack_event.payload, dict)
            else None,
            "is_ack": slack_event.is_ack,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return SlackEventDBEntity(**result)

    async def _insert(self, slack_event: SlackEventDBEntity) -> SlackEventDBEntity:
        event_id = self.generate_id()
        query = """
            insert into slack_event (
                event_id, tenant_id, slack_event_ref,
                inner_event_type, event_dispatched_ts, api_app_id,
                token, payload, is_ack
            )
            values (
                :event_id, :tenant_id, :slack_event_ref,
                :inner_event_type, :event_dispatched_ts, :api_app_id,
                :token, :payload, :is_ack
            )
            returning event_id, tenant_id, slack_event_ref,
                inner_event_type, event_dispatched_ts, api_app_id,
                token, payload, is_ack, created_at, updated_at
        """
        parameters = {
            "event_id": event_id,
            "tenant_id": slack_event.tenant_id,
            "slack_event_ref": slack_event.slack_event_ref,
            "inner_event_type": slack_event.inner_event_type,
            "event_dispatched_ts": slack_event.event_dispatched_ts,
            "api_app_id": slack_event.api_app_id,
            "token": slack_event.token,
            "payload": json.dumps(slack_event.payload)
            if isinstance(slack_event.payload, dict)
            else None,
            "is_ack": slack_event.is_ack,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return SlackEventDBEntity(**result)

    async def save(self, slack_event: SlackEventDBEntity) -> SlackEventDBEntity:
        if slack_event.event_id is None:
            return await self._insert(slack_event)
        return await self._upsert(slack_event)


class AbstractInSyncChannelRepository(abc.ABC):
    @abc.abstractmethod
    async def save(
        self, insync_channel: InSyncSlackChannelDBEntity
    ) -> InSyncSlackChannelDBEntity:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_tenant_id_id(
        self, tenant_id: str, id: str
    ) -> InSyncSlackChannelDBEntity | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_tenant_id_id(
        self, tenant_id: str, id: str
    ) -> InSyncSlackChannelDBEntity:
        raise NotImplementedError


class InSyncChannelRepository(AbstractInSyncChannelRepository, BaseRepository):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def find_by_tenant_id_id(
        self, tenant_id: str, id: str
    ) -> InSyncSlackChannelDBEntity | None:
        query = """
            select tenant_id, context_team_id, created, creator, id, is_archived,
            is_channel, is_ext_shared, is_general, is_group, is_im, is_member, is_mpim,
            is_org_shared, is_pending_ext_shared, is_private, is_shared, name,
            name_normalized, num_members, parent_conversation,
            pending_connected_team_ids, pending_shared, previous_names, purpose,
            shared_team_ids, topic, unlinked, updated, created_at, updated_at
            from insync_slack_channel
            where tenant_id = :tenant_id and id = :id
        """
        parameters = {"tenant_id": tenant_id, "id": id}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return InSyncSlackChannelDBEntity(**result)

    async def get_by_tenant_id_id(
        self, tenant_id: str, id: str
    ) -> InSyncSlackChannelDBEntity:
        channel = await self.find_by_tenant_id_id(tenant_id, id)
        if channel is None:
            raise DBNotFoundException(f"channel with id `{id}` not found")
        return channel

    async def save(
        self, insync_channel: InSyncSlackChannelDBEntity
    ) -> InSyncSlackChannelDBEntity:
        query = """
            insert into insync_slack_channel (
                tenant_id, context_team_id, created, creator, id, is_archived,
                is_channel, is_ext_shared, is_general, is_group, is_im, is_member,
                is_mpim, is_org_shared, is_pending_ext_shared, is_private, is_shared,
                name, name_normalized, num_members, parent_conversation,
                pending_connected_team_ids, pending_shared, previous_names, purpose,
                shared_team_ids, topic, unlinked, updated
            )
            values (
                :tenant_id, :context_team_id, :created, :creator, :id, :is_archived,
                :is_channel, :is_ext_shared, :is_general, :is_group, :is_im, :is_member,
                :is_mpim, :is_org_shared, :is_pending_ext_shared, :is_private,
                :is_shared, :name, :name_normalized, :num_members, :parent_conversation,
                :pending_connected_team_ids, :pending_shared, :previous_names, :purpose,
                :shared_team_ids, :topic, :unlinked, :updated
            )
            on conflict (tenant_id, id) do update set
                context_team_id = :context_team_id,
                created = :created,
                creator = :creator,
                is_archived = :is_archived,
                is_channel = :is_channel,
                is_ext_shared = :is_ext_shared,
                is_general = :is_general,
                is_group = :is_group,
                is_im = :is_im,
                is_member = :is_member,
                is_mpim = :is_mpim,
                is_org_shared = :is_org_shared,
                is_pending_ext_shared = :is_pending_ext_shared,
                is_private = :is_private,
                is_shared = :is_shared,
                name = :name,
                name_normalized = :name_normalized,
                num_members = :num_members,
                parent_conversation = :parent_conversation,
                pending_connected_team_ids = :pending_connected_team_ids,
                pending_shared = :pending_shared,
                previous_names = :previous_names,
                purpose = :purpose,
                shared_team_ids = :shared_team_ids,
                topic = :topic,
                unlinked = :unlinked,
                updated = :updated,
                updated_at = now()
            returning tenant_id, context_team_id, created, creator, id, is_archived,
                is_channel, is_ext_shared, is_general, is_group, is_im, is_member,
                is_mpim, is_org_shared, is_pending_ext_shared, is_private, is_shared,
                name, name_normalized, num_members, parent_conversation,
                pending_connected_team_ids, pending_shared, previous_names, purpose,
                shared_team_ids, topic, unlinked, updated, created_at, updated_at
        """
        purpose = (
            json.dumps(insync_channel.purpose)
            if isinstance(insync_channel.purpose, dict)
            else None
        )
        topic = (
            json.dumps(insync_channel.topic)
            if isinstance(insync_channel.topic, dict)
            else None
        )
        parameters = {
            "tenant_id": insync_channel.tenant_id,
            "context_team_id": insync_channel.context_team_id,
            "created": insync_channel.created,
            "creator": insync_channel.creator,
            "id": insync_channel.id,
            "is_archived": insync_channel.is_archived,
            "is_channel": insync_channel.is_channel,
            "is_ext_shared": insync_channel.is_ext_shared,
            "is_general": insync_channel.is_general,
            "is_group": insync_channel.is_group,
            "is_im": insync_channel.is_im,
            "is_member": insync_channel.is_member,
            "is_mpim": insync_channel.is_mpim,
            "is_org_shared": insync_channel.is_org_shared,
            "is_pending_ext_shared": insync_channel.is_pending_ext_shared,
            "is_private": insync_channel.is_private,
            "is_shared": insync_channel.is_shared,
            "name": insync_channel.name,
            "name_normalized": insync_channel.name_normalized,
            "num_members": insync_channel.num_members,
            "parent_conversation": insync_channel.parent_conversation,
            "pending_connected_team_ids": insync_channel.pending_connected_team_ids
            if isinstance(insync_channel.pending_connected_team_ids, list)
            and len(insync_channel.pending_connected_team_ids)
            else None,
            "pending_shared": insync_channel.pending_shared
            if isinstance(insync_channel.pending_shared, list)
            and len(insync_channel.pending_shared)
            else None,
            "previous_names": insync_channel.previous_names
            if isinstance(insync_channel.previous_names, list)
            and len(insync_channel.previous_names)
            else None,
            "purpose": purpose,
            "shared_team_ids": insync_channel.shared_team_ids
            if isinstance(insync_channel.shared_team_ids, list)
            and len(insync_channel.shared_team_ids)
            else None,
            "topic": topic,
            "unlinked": insync_channel.unlinked,
            "updated": insync_channel.updated,
        }

        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return InSyncSlackChannelDBEntity(**result)


class AbstractSlackChannelRepository(abc.ABC):
    @abc.abstractmethod
    async def save(
        self, linked_channel: SlackChannelDBEntity
    ) -> SlackChannelDBEntity:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_slack_channel_id(
        self, slack_channel_id: str
    ) -> SlackChannelDBEntity | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_slack_channel_id(slack_channel_id: str):
        raise NotImplementedError


class SlackChannelRepository(
    AbstractSlackChannelRepository, BaseRepository
):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def _upsert(
        self, linked_channel: SlackChannelDBEntity
    ) -> SlackChannelDBEntity:
        query = """
            insert into slack_channel (
                tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name,
                triage_slack_channel_ref, triage_slack_channel_name
            )
            values (
                :tenant_id, :slack_channel_id, :slack_channel_ref,
                :slack_channel_name,
                :triage_slack_channel_ref, :triage_slack_channel_name
            )
            on conflict (slack_channel_id) do update set
                tenant_id = :tenant_id,
                slack_channel_ref = :slack_channel_ref,
                slack_channel_name = :slack_channel_name,
                triage_slack_channel_ref = :triage_slack_channel_ref,
                triage_slack_channel_name = :triage_slack_channel_name,
                updated_at = now()
            returning tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
        """
        parameters = {
            "tenant_id": linked_channel.tenant_id,
            "slack_channel_id": linked_channel.slack_channel_id,
            "slack_channel_ref": linked_channel.slack_channel_ref,
            "slack_channel_name": linked_channel.slack_channel_name,
            "triage_slack_channel_ref": linked_channel.triage_slack_channel_ref,
            "triage_slack_channel_name": linked_channel.triage_slack_channel_name,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return SlackChannelDBEntity(**result)

    async def _insert(
        self, linked_channel: SlackChannelDBEntity
    ) -> SlackChannelDBEntity:
        slack_channel_id = self.generate_id()
        query = """
            insert into slack_channel (
                tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name,
                triage_slack_channel_ref, triage_slack_channel_name
            )
            values (
                :tenant_id, :slack_channel_id, :slack_channel_ref,
                :slack_channel_name,
                :triage_slack_channel_ref, :triage_slack_channel_name
            )
            returning tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
        """
        parameters = {
            "tenant_id": linked_channel.tenant_id,
            "slack_channel_id": slack_channel_id,
            "slack_channel_ref": linked_channel.slack_channel_ref,
            "slack_channel_name": linked_channel.slack_channel_name,
            "triage_slack_channel_ref": linked_channel.triage_slack_channel_ref,
            "triage_slack_channel_name": linked_channel.triage_slack_channel_name,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return SlackChannelDBEntity(**result)

    async def save(
        self, linked_channel: SlackChannelDBEntity
    ) -> SlackChannelDBEntity:
        if linked_channel.slack_channel_id is None:
            return await self._insert(linked_channel)
        return await self._upsert(linked_channel)

    async def find_by_slack_channel_id(
        self, slack_channel_id: str
    ) -> SlackChannelDBEntity | None:
        query = """
            select tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
            from slack_channel
            where slack_channel_id = :slack_channel_id
        """
        parameters = {
            "slack_channel_id": slack_channel_id,
        }
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return SlackChannelDBEntity(**result)

    async def get_by_slack_channel_id(
        self, slack_channel_id: str
    ) -> SlackChannelDBEntity:
        linked_channel = await self.find_by_slack_channel_id(
            slack_channel_id
        )
        if linked_channel is None:
            raise DBNotFoundException(
                f"linked channel with id `{slack_channel_id}` not found"
            )
        return linked_channel

    async def find_by_slack_channel_ref(
        self, slack_channel_ref: str
    ) -> SlackChannelDBEntity | None:
        query = """
            select tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
            from slack_channel
            where slack_channel_ref = :slack_channel_ref
        """
        parameters = {
            "slack_channel_ref": slack_channel_ref,
        }
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return SlackChannelDBEntity(**result)

    async def get_by_slack_channel_ref(
        self, slack_channel_ref: str
    ) -> SlackChannelDBEntity:
        linked_channel = await self.find_by_slack_channel_ref(slack_channel_ref)
        if linked_channel is None:
            raise DBNotFoundException(
                f"linked channel with ref `{slack_channel_ref}` not found"
            )
        return linked_channel

    async def find_by_tenant_id_slack_channel_name(
        self, tenant_id: str, slack_channel_name: str
    ) -> SlackChannelDBEntity:
        query = """
            select tenant_id, slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
            from slack_channel
            where tenant_id = :tenant_id and slack_channel_name = :slack_channel_name
        """
        parameters = {
            "tenant_id": tenant_id,
            "slack_channel_name": slack_channel_name,
        }
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return SlackChannelDBEntity(**result)


class AbstractIssueRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, issue: IssueDBEntity) -> dict:
        raise NotImplementedError


class IssueRepository(AbstractIssueRepository, BaseRepository):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def _insert(self, issue: IssueDBEntity) -> IssueDBEntity:
        issue_id = self.generate_id()
        query = """
            with sequencer as (
                insert into issue_seq (tenant_id)
                values (:tenant_id) on conflict (tenant_id)
                do update set 
                    seq = (
                        select seq + 1 as seq
                        from issue_seq
                        where
                        tenant_id = :tenant_id
                    ),
                    updated_at = now()
                returning seq
            )
            insert into issue (
                issue_id, tenant_id, body, status, priority, tags, issue_number,
                slack_channel_id
            ) values (
                :issue_id, :tenant_id, :body, :status, :priority, :tags, (
                    select seq from sequencer
                ), :slack_channel_id
            )
            returning issue_id, tenant_id, body, status, priority, tags,
            issue_number, slack_channel_id, created_at, updated_at;
        """
        parameters = {
            "issue_id": issue_id,
            "tenant_id": issue.tenant_id,
            "body": issue.body,
            "status": issue.status,
            "priority": issue.priority,
            "tags": issue.tags
            if isinstance(issue.tags, list) and len(issue.tags)
            else None,
            "slack_channel_id": issue.slack_channel_id,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return IssueDBEntity(**result)
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)

    async def _upsert(self, issue: IssueDBEntity) -> IssueDBEntity:
        query = """
            insert into issue (
                issue_id, tenant_id, body, status, priority, tags, issue_number,
                slack_channel_id
            ) values (
                :issue_id, :tenant_id, :body, :status, :priority, :tags, :issue_number,
                :slack_channel_id
            )
            on conflict (issue_id) do update set
                tenant_id = :tenant_id,
                body = :body,
                status = :status,
                priority = :priority,
                tags = :tags,
                issue_number = :issue_number,
                slack_channel_id = :slack_channel_id,
                updated_at = now()
            returning issue_id, tenant_id, body, status, priority, tags,
            issue_number, created_at, updated_at
        """
        parameters = {
            "issue_id": issue.issue_id,
            "tenant_id": issue.tenant_id,
            "body": issue.body,
            "status": issue.status,
            "priority": issue.priority,
            "tags": issue.tags
            if isinstance(issue.tags, list) and len(issue.tags)
            else None,
            "issue_number": issue.issue_number,
            "slack_channel_id": issue.slack_channel_id,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return IssueDBEntity(**result)
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)

    async def save(self, issue: IssueDBEntity) -> IssueDBEntity:
        if issue.issue_id is None:
            return await self._insert(issue)
        return await self._upsert(issue)


class InSyncSlackUserAbstractRepository(abc.ABC):
    @abc.abstractmethod
    async def save(
        self, insync_user: InSyncSlackUserDBEntity
    ) -> InSyncSlackUserDBEntity:
        raise NotImplementedError


class InSyncSlackUserRepository(InSyncSlackUserAbstractRepository, BaseRepository):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def save(
        self, insync_user: InSyncSlackUserDBEntity
    ) -> InSyncSlackUserDBEntity:
        query = """
            insert into insync_slack_user (
                tenant_id, id, is_admin, is_app_user, is_bot, is_email_confirmed,
                is_owner, is_primary_owner, is_restricted, is_ultra_restricted, name,
                profile, real_name, team_id, tz, tz_label, tz_offset, updated
            )
            values (
                :tenant_id, :id, :is_admin, :is_app_user, :is_bot, :is_email_confirmed,
                :is_owner, :is_primary_owner, :is_restricted, :is_ultra_restricted,
                :name, :profile, :real_name, :team_id, :tz, :tz_label, :tz_offset,
                :updated
            )
            on conflict (tenant_id, id) do update set
                is_admin = :is_admin,
                is_app_user = :is_app_user,
                is_bot = :is_bot,
                is_email_confirmed = :is_email_confirmed,
                is_owner = :is_owner,
                is_primary_owner = :is_primary_owner,
                is_restricted = :is_restricted,
                is_ultra_restricted = :is_ultra_restricted,
                name = :name,
                profile = :profile,
                real_name = :real_name,
                team_id = :team_id,
                tz = :tz,
                tz_label = :tz_label,
                tz_offset = :tz_offset,
                updated = :updated,
                updated_at = now()
            returning tenant_id, id, is_admin, is_app_user, is_bot, is_email_confirmed,
                is_owner, is_primary_owner, is_restricted, is_ultra_restricted, name,
                profile, real_name, team_id, tz, tz_label, tz_offset, updated,
                created_at, updated_at
        """
        profile = (
            json.dumps(insync_user.profile)
            if isinstance(insync_user.profile, dict)
            else None
        )
        parameters = {
            "tenant_id": insync_user.tenant_id,
            "id": insync_user.id,
            "is_admin": insync_user.is_admin,
            "is_app_user": insync_user.is_app_user,
            "is_bot": insync_user.is_bot,
            "is_email_confirmed": insync_user.is_email_confirmed,
            "is_owner": insync_user.is_owner,
            "is_primary_owner": insync_user.is_primary_owner,
            "is_restricted": insync_user.is_restricted,
            "is_ultra_restricted": insync_user.is_ultra_restricted,
            "name": insync_user.name,
            "profile": profile,
            "real_name": insync_user.real_name,
            "team_id": insync_user.team_id,
            "tz": insync_user.tz,
            "tz_label": insync_user.tz_label,
            "tz_offset": insync_user.tz_offset,
            "updated": insync_user.updated,
        }

        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return InSyncSlackUserDBEntity(**result)


class AbstractUserRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, user: UserDBEntity) -> UserDBEntity:
        raise NotImplementedError


class UserRepository(AbstractUserRepository, BaseRepository):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def _upsert(self, user: UserDBEntity) -> UserDBEntity:
        query = """
            insert into zyguser (
                user_id, tenant_id, slack_user_ref, name, role
            )
            values (
                :user_id, :tenant_id, :slack_user_ref, :name, :role
            )
            on conflict (user_id) do update set
                tenant_id = :tenant_id,
                slack_user_ref = :slack_user_ref,
                name = :name,
                role = :role,
                updated_at = now()
            returning user_id, tenant_id, slack_user_ref, name, role,
            created_at, updated_at
        """
        parameters = {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "slack_user_ref": user.slack_user_ref,
            "name": user.name,
            "role": user.role,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return UserDBEntity(**result)

    async def _insert(self, user: UserDBEntity) -> UserDBEntity:
        user_id = self.generate_id()
        query = """
            insert into zyguser (
                user_id, tenant_id, slack_user_ref, name, role
            )
            values (
                :user_id, :tenant_id, :slack_user_ref, :name, :role
            )
            returning user_id, tenant_id, slack_user_ref, name, role,
            created_at, updated_at
        """
        parameters = {
            "user_id": user_id,
            "tenant_id": user.tenant_id,
            "slack_user_ref": user.slack_user_ref,
            "name": user.name,
            "role": user.role,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            # We are raising `DBIntegrityException` here
            # to maintain common exception handling for database related
            # exceptions, this makes sure that we are not leaking
            # database related exceptions to the downstream layers
            #
            # Having custom exceptions for database related exceptions
            # also helps us to have a better control over the error handling.
            raise DBIntegrityException(e)
        return UserDBEntity(**result)

    async def save(self, user: UserDBEntity) -> UserDBEntity:
        if user.user_id is None:
            return await self._insert(user)
        return await self._upsert(user)

    async def upsert_by_tenant_id_slack_user_ref(
        self, user: UserDBEntity
    ) -> UserDBEntity:
        user_id = user.user_id if user.user_id is not None else self.generate_id()
        query = """
            insert into zyguser (
                user_id, tenant_id, slack_user_ref, name, role
            )
            values (
                :user_id, :tenant_id, :slack_user_ref, :name, :role
            )
            on conflict (tenant_id, slack_user_ref) do update set
                name = :name,
                updated_at = now()
            returning user_id, tenant_id, slack_user_ref, name, role,
            created_at, updated_at
        """
        parameters = {
            "user_id": user_id,
            "tenant_id": user.tenant_id,
            "slack_user_ref": user.slack_user_ref,
            "name": user.name,
            "role": user.role,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
        except IntegrityError as e:
            raise DBIntegrityException(e)
        return UserDBEntity(**result)

    async def find_by_user_id(self, user_id: str) -> UserDBEntity | None:
        query = """
            select user_id, tenant_id, slack_user_ref, name, role,
            created_at, updated_at
            from zyguser
            where user_id = :user_id
        """
        parameters = {"user_id": user_id}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return UserDBEntity(**result)

    async def find_by_tenant_id_slack_user_ref(
        self, tenant_id: str, slack_user_ref: str
    ) -> UserDBEntity | None:
        query = """
            select user_id, tenant_id, slack_user_ref, name, role,
            created_at, updated_at
            from zyguser
            where tenant_id = :tenant_id and slack_user_ref = :slack_user_ref
        """
        parameters = {"tenant_id": tenant_id, "slack_user_ref": slack_user_ref}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return UserDBEntity(**result)

    async def get_by_id(self, user_id: str) -> UserDBEntity:
        user = await self.find_by_user_id(user_id)
        if user is None:
            raise DBNotFoundException(f"user with id `{user_id}` not found")
        return user

    async def get_by_tenant_id_slack_user_ref(
        self, tenant_id: str, slack_user_ref: str
    ):
        user = await self.find_by_tenant_id_slack_user_ref(tenant_id, slack_user_ref)
        if user is None:
            raise DBNotFoundException(
                f"user with tenant_id `{tenant_id}` "
                "and slack_user_ref `{slack_user_ref}` not found"
            )
        return user
