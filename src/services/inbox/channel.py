from src.adapters.db.adapters import SlackChannelDBAdapter
from src.domain.commands import CreateSlackChannelCommand
from src.domain.models import SlackChannel
from src.logger import logger
from src.services.inbox.exceptions import SlackChannelDuplicateException


class SlackChannelService:
    def __init__(self) -> None:
        self.db_adapter = SlackChannelDBAdapter()

    async def create(self, command: CreateSlackChannelCommand):
        logger.info(f"`create` slack channel service invoked with command: `{command}`")
        if command.channel_id is None:
            new_slack_channel = SlackChannel(
                channel_id=None,
                name=command.name,
                channel_type=command.channel_type,
            )
            return await self.db_adapter.save(new_slack_channel)

        is_channel_exists = await self.db_adapter.is_channel_exists(command.channel_id)
        if is_channel_exists:
            raise SlackChannelDuplicateException(
                f"slack channel with channel_id: {command.channel_id} "
                + "already exists.",
            )

        new_slack_channel = SlackChannel(
            channel_id=command.channel_id,
            name=command.name,
            channel_type=command.channel_type,
        )
        return await self.db_adapter.save(new_slack_channel)
