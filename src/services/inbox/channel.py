from src.adapters.db.adapters import SlackChannelDBAdapter
from src.domain.commands import CreateSlackChannelCommand
from src.logger import logger
from src.domain.models import SlackChannel


class SlackChannelService:
    def __init__(self) -> None:
        self.db_adapter = SlackChannelDBAdapter()

    async def create(self, command: CreateSlackChannelCommand):
        logger.info(f"`create` slack channel service invoked with command: `{command}`")
        if command.channel_id is None:
            channel_id = None
        else:
            channel_id = command.channel_id
        new_slack_channel = SlackChannel(
            channel_id=channel_id,
            name=command.name,
            channel_type=command.channel_type,
        )
        return await self.db_adapter.save(new_slack_channel)
