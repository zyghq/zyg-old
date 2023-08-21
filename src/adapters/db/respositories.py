import abc
import json

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from .entities import SlackEventDbEntity
from .exceptions import DBIntegrityException


class AbstractSlackEventRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, slack_event: SlackEventDbEntity):
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

    async def upsert(self, new_slack_event: SlackEventDbEntity) -> SlackEventDbEntity:
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

    async def get(self, event_id: str):
        raise NotImplementedError
