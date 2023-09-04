import abc
import json
import random
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from .entities import SlackEventDBEntity, TenantDBEntity
from .exceptions import DBIntegrityException


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
    def __init__(self, connection):
        self.conn = connection

    async def find_by_slack_team_ref(
        self, slack_team_ref: str
    ) -> TenantDBEntity | None:
        query = """
            select tenant_id, name, created_at, updated_at
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
            select tenant_id, name, created_at, updated_at
            from tenant
            where tenant_id = :tenant_id
        """
        parameters = {"tenant_id": tenant_id}
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return TenantDBEntity(**result)

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
                tenant_id = :tenant_id
                name = :name
                slack_team_ref = :slack_team_ref
                updated_at = now()
            returning tenant_id, name, slack_team_ref, created_at, updated_at
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
            returning tenant_id, name, slack_team_ref, created_at, updated_at
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
    def __init__(self, connection) -> None:
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
