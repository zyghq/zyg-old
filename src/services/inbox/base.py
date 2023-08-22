from src.adapters.db.adapters import InboxDBAdapter
from src.domain.commands import CreateInboxCommand
from src.logger import logger
from src.domain.models import Inbox


class InboxService:
    def __init__(self) -> None:
        self.inbox_db_adapter = InboxDBAdapter()

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
        else:
            raise NotImplementedError
