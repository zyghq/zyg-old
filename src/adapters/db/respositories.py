import abc
import json
import random
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from .entities import InboxDbEntity, SlackEventDbEntity
from .exceptions import DBIntegrityException


class BaseRepository:
    @classmethod
    def generate_id(cls, length=12, lowercase=True):
        result = "".join(random.choices(string.ascii_letters + string.digits, k=length))
        if lowercase:
            return result.lower()
        return result


class AbstractSlackEventRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, new_slack_event: SlackEventDbEntity):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, event_id: str):
        raise NotImplementedError


class SlackEventRepository(AbstractSlackEventRepository):
    def __init__(self, connection) -> None:
        self.conn = connection

    async def add(self, new_slack_event: SlackEventDbEntity) -> SlackEventDbEntity:
        query = f"""
            insert into slack_event (
                event_id, team_id, event, event_type, 
                event_ts, metadata
            )
            values (
                :event_id, :team_id, :event, :event_type, 
                :event_ts, :metadata
            )
            returning event_id, team_id, event, event_type, 
                event_ts, metadata, created_at, updated_at, is_ack
        """
        parameters = {
            "event_id": new_slack_event.event_id,
            "team_id": new_slack_event.team_id,
            "event": json.dumps(new_slack_event.event)
            if isinstance(new_slack_event.event, dict)
            else None,
            "event_type": new_slack_event.event_type,
            "event_ts": new_slack_event.event_ts,
            "metadata": json.dumps(new_slack_event.metadata)
            if isinstance(new_slack_event.metadata, dict)
            else None,
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
        return SlackEventDbEntity(**result)

    async def upsert(self, slack_event: SlackEventDbEntity) -> SlackEventDbEntity:
        query = f"""
            insert into slack_event (
                event_id, team_id, event, event_type, 
                event_ts, metadata
            )
            values (
                :event_id, :team_id, :event, :event_type, 
                :event_ts, :metadata
            )
            on conflict (event_id) do update set
                team_id = :team_id,
                event = :event,
                event_type = :event_type,
                event_ts = :event_ts,
                metadata = :metadata
            returning event_id, team_id, event, event_type, 
                event_ts, metadata, created_at, updated_at, is_ack
        """
        parameters = {
            "event_id": slack_event.event_id,
            "team_id": slack_event.team_id,
            "event": json.dumps(slack_event.event)
            if isinstance(slack_event.event, dict)
            else None,
            "event_type": slack_event.event_type,
            "event_ts": slack_event.event_ts,
            "metadata": json.dumps(slack_event.metadata)
            if isinstance(slack_event.metadata, dict)
            else None,
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
        return SlackEventDbEntity(**result)

    async def get(self, event_id: str):
        raise NotImplementedError


class AbstractInboxRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, inbox: InboxDbEntity):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, inbox_id: str):
        raise NotImplementedError


class InboxRepository(AbstractInboxRepository, BaseRepository):
    def __init__(self, connection) -> None:
        self.conn = connection

    async def add(self, new_inbox: InboxDbEntity) -> InboxDbEntity:
        query = f"""
            insert into inbox (
                inbox_id, name, description, slack_channel_id
            )
            values (
                :inbox_id, :name, :description, :slack_channel_id
            )
            returning inbox_id, name, description, slack_channel_id, created_at, updated_at
        """
        parameters = {
            "inbox_id": new_inbox.inbox_id,
            "name": new_inbox.name,
            "description": new_inbox.description,
            "slack_channel_id": new_inbox.slack_channel_id,
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
        return InboxDbEntity(**result)

    async def get(self, inbox_id: str):
        raise NotImplementedError
