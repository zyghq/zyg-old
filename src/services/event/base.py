from src.adapters.db.adapters import SlackEventDBAdapter
from src.adapters.db.exceptions import DBIntegrityException
from src.domain.commands import CreateSlackEventCommand
from src.domain.models import SlackCallbackEvent
from src.logger import logger

from .exceptions import SlackEventDBException


class SlackEventCaptureService:
    def __init__(self) -> None:
        self.slack_event_db_adapter = SlackEventDBAdapter()

    async def capture(
        self, command: CreateSlackEventCommand, override=False
    ) -> SlackCallbackEvent:
        logger.info(f"`capture` slack event service invoked with command: `{command}`")
        try:
            slack_event = SlackCallbackEvent(
                event_id=command.event_id,
                team_id=command.team_id,
                event=command.event,
                event_type=command.event_type,
                event_ts=command.event_ts,
                metadata=command.metadata,
            )
            if override:
                logger.warning(
                    f"override slack event for event_id: `{command.event_id}`"
                )
                result = await self.slack_event_db_adapter.update(slack_event)
            else:
                result = await self.slack_event_db_adapter.save(slack_event)
            return result
        except DBIntegrityException as e:
            logger.error(e)
            raise SlackEventDBException("error when capturing slack event.")


class SlackEventChannelMesssageService:
    async def execute(self, slack_event: SlackCallbackEvent):
        print("**********************************")
        print("handle execute command for message")
        print(slack_event)
        print("**********************************")
