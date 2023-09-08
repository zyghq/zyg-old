import abc
import json
import random
import string

from sqlalchemy import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from .entities import (
    InSyncSlackChannelDBEntity,
    LinkedSlackChannelDBEntity,
    SlackEventDBEntity,
    TenantDBEntity,
)
from .exceptions import DBIntegrityException, DBNotFoundException


class BaseRepository:
    @classmethod
    def generate_id(cls, length=12, lowercase=True):
        result = "".join(random.choices(string.ascii_letters + string.digits, k=length))
        if lowercase:
            return result.lower()
        return result


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
                inner_event_type, event, event_ts, api_app_id,
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
                inner_event_type, event, event_ts, api_app_id,
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
                inner_event_type, event, event_ts, api_app_id,
                token, payload, is_ack
            )
            values (
                :event_id, :tenant_id, :slack_event_ref,
                :inner_event_type, :event, :event_ts, :api_app_id,
                :token, :payload, :is_ack
            )
            on conflict (event_id) do update set
                tenant_id = :tenant_id,
                slack_event_ref = :slack_event_ref,
                inner_event_type = :inner_event_type,
                event = :event,
                event_ts = :event_ts,
                api_app_id = :api_app_id,
                token = :token,
                payload = :payload,
                is_ack = :is_ack,
                updated_at = now()
            returning event_id, tenant_id, slack_event_ref,
                inner_event_type, event, event_ts, api_app_id,
                token, payload, is_ack, created_at, updated_at
        """
        parameters = {
            "event_id": slack_event.event_id,
            "tenant_id": slack_event.tenant_id,
            "slack_event_ref": slack_event.slack_event_ref,
            "inner_event_type": slack_event.inner_event_type,
            "event": json.dumps(slack_event.event)
            if isinstance(slack_event.event, dict)
            else None,
            "event_ts": slack_event.event_ts,
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
                inner_event_type, event, event_ts, api_app_id,
                token, payload, is_ack
            )
            values (
                :event_id, :tenant_id, :slack_event_ref,
                :inner_event_type, :event, :event_ts, :api_app_id,
                :token, :payload, :is_ack
            )
            returning event_id, tenant_id, slack_event_ref,
                inner_event_type, event, event_ts, api_app_id,
                token, payload, is_ack, created_at, updated_at
        """
        parameters = {
            "event_id": event_id,
            "tenant_id": slack_event.tenant_id,
            "slack_event_ref": slack_event.slack_event_ref,
            "inner_event_type": slack_event.inner_event_type,
            "event": json.dumps(slack_event.event)
            if isinstance(slack_event.event, dict)
            else None,
            "event_ts": slack_event.event_ts,
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
        self, channel: InSyncSlackChannelDBEntity
    ) -> InSyncSlackChannelDBEntity:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_tenant_id_id(
        self, tenant_id: str, id: str
    ) -> InSyncSlackChannelDBEntity | None:
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
            # query = text(query)
            # rows = await self.conn.execute(query.bindparams(**parameters))
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


class AbstractLinkedSlackChannelRepository(abc.ABC):
    @abc.abstractmethod
    async def save(
        self, linked_channel: LinkedSlackChannelDBEntity
    ) -> LinkedSlackChannelDBEntity:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_linked_slack_channel_id(
        self, linked_slack_channel_id: str
    ) -> LinkedSlackChannelDBEntity | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_by_linked_slack_channel_id(linked_slack_channel_id: str):
        raise NotImplementedError


class LinkedSlackChannelRepository(
    AbstractLinkedSlackChannelRepository, BaseRepository
):
    def __init__(self, connection: Connection) -> None:
        self.conn = connection

    async def _upsert(
        self, linked_channel: LinkedSlackChannelDBEntity
    ) -> LinkedSlackChannelDBEntity:
        query = """
            insert into linked_slack_channel (
                tenant_id, linked_slack_channel_id, slack_channel_ref,
                slack_channel_name,
                triage_slack_channel_ref, triage_slack_channel_name
            )
            values (
                :tenant_id, :linked_slack_channel_id, :slack_channel_ref,
                :slack_channel_name,
                :triage_slack_channel_ref, :triage_slack_channel_name
            )
            on conflict (linked_slack_channel_id) do update set
                tenant_id = :tenant_id,
                slack_channel_ref = :slack_channel_ref,
                slack_channel_name = :slack_channel_name,
                triage_slack_channel_ref = :triage_slack_channel_ref,
                triage_slack_channel_name = :triage_slack_channel_name,
                updated_at = now()
            returning tenant_id, linked_slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
        """
        parameters = {
            "tenant_id": linked_channel.tenant_id,
            "linked_slack_channel_id": linked_channel.linked_slack_channel_id,
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
        return LinkedSlackChannelDBEntity(**result)

    async def _insert(
        self, linked_channel: LinkedSlackChannelDBEntity
    ) -> LinkedSlackChannelDBEntity:
        linked_slack_channel_id = self.generate_id()
        query = """
            insert into linked_slack_channel (
                tenant_id, linked_slack_channel_id, slack_channel_ref,
                slack_channel_name,
                triage_slack_channel_ref, triage_slack_channel_name
            )
            values (
                :tenant_id, :linked_slack_channel_id, :slack_channel_ref,
                :slack_channel_name,
                :triage_slack_channel_ref, :triage_slack_channel_name
            )
            returning tenant_id, linked_slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
        """
        parameters = {
            "tenant_id": linked_channel.tenant_id,
            "linked_slack_channel_id": linked_slack_channel_id,
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
        return LinkedSlackChannelDBEntity(**result)

    async def save(
        self, linked_channel: LinkedSlackChannelDBEntity
    ) -> LinkedSlackChannelDBEntity:
        if linked_channel.linked_slack_channel_id is None:
            return await self._insert(linked_channel)
        return await self._upsert(linked_channel)

    async def find_by_linked_slack_channel_id(
        self, linked_slack_channel_id: str
    ) -> LinkedSlackChannelDBEntity | None:
        query = """
            select tenant_id, linked_slack_channel_id, slack_channel_ref,
                slack_channel_name, triage_slack_channel_ref, triage_slack_channel_name,
                created_at, updated_at
            from linked_slack_channel
            where linked_slack_channel_id = :linked_slack_channel_id
        """
        parameters = {
            "linked_slack_channel_id": linked_slack_channel_id,
        }
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return LinkedSlackChannelDBEntity(**result)

    async def get_by_linked_slack_channel_id(
        self, linked_slack_channel_id: str
    ) -> LinkedSlackChannelDBEntity:
        linked_channel = await self.find_by_linked_slack_channel_id(
            linked_slack_channel_id
        )
        if linked_channel is None:
            raise DBNotFoundException(
                f"linked channel with id `{linked_slack_channel_id}` not found"
            )
        return linked_channel
