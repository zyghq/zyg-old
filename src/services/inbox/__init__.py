from src.adapters.db.adapters import InboxDBAdapter
from src.domain.commands.inbox import CreateInboxCommand
from src.logger import logger
from src.domain.models import Inbox


class InboxService:
    def __init__(self) -> None:
        self.inbox_db_adapter = InboxDBAdapter()

    async def create(self, inbox: CreateInboxCommand):
        logger.info(f"`create` inbox service invoked with command: `{inbox}`")
        if inbox.slack_channel_id is None:
            new_inbox = Inbox(
                inbox_id=None,  # creating new inbox, so no inbox_id yet.
                name=inbox.name,
                description=inbox.description,
                slack_channel=None,
            )
            return await self.inbox_db_adapter.save(new_inbox)
        else:
            raise NotImplementedError
