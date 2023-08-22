from sqlalchemy.engine.base import Engine

from src.adapters.db import engine
from src.domain.models import Inbox, SlackChannel

from .entities import InboxDbEntity, SlackChannelDBEntity
from .respositories import InboxRepository, SlackChannelRepository


class InboxDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(self, inbox: Inbox) -> InboxDbEntity:
        if inbox.inbox_id is None:
            inbox_id = InboxRepository.generate_id()
        if inbox.slack_channel is None:
            slack_channel_id = None
        else:
            # TODO: map slack channel to db entity
            raise NotImplementedError("TODO: map slack channel to db entity")
        return InboxDbEntity(
            inbox_id=inbox_id,
            name=inbox.name,
            description=inbox.description,
            slack_channel_id=slack_channel_id,
        )

    def _map_to_domain(
        self,
        inbox_entity: InboxDbEntity,
        slack_channel_entity: SlackChannelDBEntity | None,
    ) -> Inbox:
        if slack_channel_entity is None:
            slack_channel = None
        return Inbox(
            inbox_id=inbox_entity.inbox_id,
            name=inbox_entity.name,
            description=inbox_entity.description,
            slack_channel=slack_channel,
        )

    async def load_channel(self, channel_id: str) -> SlackChannel:
        raise NotImplementedError

    async def save(self, inbox: Inbox) -> Inbox:
        db_entity = self._map_to_db_entity(inbox)
        async with self.engine.begin() as conn:
            inbox_entity = await InboxRepository(conn).add(db_entity)
            if inbox_entity.slack_channel_id is None:
                result = self._map_to_domain(inbox_entity, None)
            else:
                raise NotImplementedError
        return result


class SlackChannelDBAdapter:
    def __init__(self, engine: Engine = engine) -> None:
        self.engine = engine

    def _map_to_db_entity(self, slack_channel: SlackChannel) -> SlackChannelDBEntity:
        if slack_channel.channel_id is None:
            channel_id = SlackChannelRepository.generate_id()
        else:
            channel_id = slack_channel.channel_id
        return SlackChannelDBEntity(
            channel_id=channel_id,
            name=slack_channel.name,
            channel_type=slack_channel.channel_type,
        )

    def _map_to_domain(
        self, slack_channel_entity: SlackChannelDBEntity
    ) -> SlackChannel:
        return SlackChannel(
            channel_id=slack_channel_entity.channel_id,
            name=slack_channel_entity.name,
            channel_type=slack_channel_entity.channel_type,
        )

    async def save(self, slack_channel: SlackChannel) -> SlackChannel:
        db_entity = self._map_to_db_entity(slack_channel)
        async with self.engine.begin() as conn:
            slack_channel_entity = await SlackChannelRepository(conn).add(db_entity)
            result = self._map_to_domain(slack_channel_entity)
        return result
