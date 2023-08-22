from src.adapters.db.adapters import InboxDBAdapter, SlackChannelDBAdapter
from src.domain.commands import CreateInboxCommand
from src.domain.models import Inbox
from src.logger import logger

from .exceptions import SlackChannelLinkException, SlackChannelNotFoundException


class InboxService:
    def __init__(self) -> None:
        self.inbox_db_adapter = InboxDBAdapter()
        self.slack_channel_db_adapter = SlackChannelDBAdapter()

    def is_channel_linked(self, slack_channel_id: str) -> bool:
        return self.inbox_db_adapter.is_slack_channel_id_linked(slack_channel_id)

    async def create(self, command: CreateInboxCommand):
        logger.info(f"`create` inbox service invoked with command: `{command}`")
        if command.slack_channel_id is None:
            new_inbox = Inbox(
                inbox_id=None,  # creating new inbox, so no inbox_id yet.
                name=command.name,
                description=command.description,
                slack_channel=None,
            )
            return await self.inbox_db_adapter.save(new_inbox)

        is_slack_channel_linked = await self.is_channel_linked(command.slack_channel_id)
        if is_slack_channel_linked:
            raise SlackChannelLinkException(
                f"slack channel with channel_id: {command.slack_channel_id} is already linked to an inbox"
            )
        slack_channel = await self.slack_channel_db_adapter.load(
            command.slack_channel_id
        )
        if slack_channel is None:
            raise SlackChannelNotFoundException(
                f"slack channel with channel_id: {command.slack_channel_id} not found"
            )
        new_inbox = Inbox(
            inbox_id=None,  # creating new inbox, so no inbox_id yet.
            name=command.name,
            description=command.description,
            slack_channel=slack_channel,
        )
        return await self.inbox_db_adapter.save(new_inbox)
