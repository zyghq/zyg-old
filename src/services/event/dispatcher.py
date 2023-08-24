from collections import defaultdict

from src.domain.commands import CreateSlackEventCommand
from src.domain.models import SlackCallbackEvent
from src.logger import logger

from .base import SlackEventCaptureService, SlackEventChannelMesssageService


class SilentlyNotifyUnsupportedSlackEvent:
    """
    Fallback service for unsupported slack events.
    """

    async def execute(self, slack_event: SlackCallbackEvent):
        event_id = slack_event.event_id
        event_type = slack_event.event_type  # inner type
        logger.error(
            'unsupported slack event id: "%s" and event type: "%s"',
            event_id,
            event_type,
        )


class SlackEventServiceDispatcher:
    dispatcher = defaultdict(
        lambda: SilentlyNotifyUnsupportedSlackEvent,
        {
            "message.channels": SlackEventChannelMesssageService,
        },
    )

    def __init__(self, command: CreateSlackEventCommand, override=False) -> None:
        self.command = command
        self.override = override

    async def _capture_with_override(self) -> SlackCallbackEvent:
        event_capture_service = SlackEventCaptureService()
        return await event_capture_service.capture(self.command, override=True)

    async def _capture_without_override(self) -> SlackCallbackEvent:
        event_capture_service = SlackEventCaptureService()
        return await event_capture_service.capture(self.command)

    async def dispatch(self):
        """
        Dispatches the Slack event to the appropriate service, based on
        the inner `type`.

        This is different from the outer `type` which is more appropriately
        can be called callback type.
        """

        logger.info(
            f"callback event dispatch for event_id: {self.command.event_id} "
            + f"and team_id: {self.command.team_id}"
        )

        if self.override:
            slack_event = await self._capture_with_override()
        else:
            slack_event = await self._capture_without_override()

        event_type = self.command.event_type
        event = self.command.event

        if event_type == "message" and "channel_type" in event:
            channel_type = event.get("channel_type")
            if channel_type == "channel":
                dispatch_key = "message.channels"
                return await self.dispatcher[dispatch_key]().execute(slack_event)
            else:
                logger.error(
                    "channel type is not a channel "
                    + f"add support for channel type: {channel_type}"
                )
        else:
            logger.error('unsupported slack event type: "%s"', event_type)
        return await self.dispatcher["unsupported"]().execute(slack_event)
