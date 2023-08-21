from collections import defaultdict

from src.domain.commands.events import SlackEventCommand
from src.logger import logger

from .base import SlackEventCaptureService
from .message import SlackEventChannelMesssageService


class UnRegisteredSlackEventTypeException(Exception):
    pass


class SilentlyNotifyUnsupportedSlackEvent:
    """
    Fallback service for unsupported slack events.
    """

    def execute(self, command: SlackEventCommand):
        event_type = command.event_type  # inner type
        event = command.event  # inner event dict
        event_subtype = event.get("subtype", "n/a")
        logger.error(
            'unsupported slack event type: "%s" and subtype: "%s"',
            event_type,
            event_subtype,
        )


class SlackEventServiceDispatcher:
    dispatcher = defaultdict(
        lambda: SilentlyNotifyUnsupportedSlackEvent,
        {
            "message.channels": SlackEventChannelMesssageService,
        },
    )

    def __init__(
        self, command: SlackEventCommand, capture=True, override=False
    ) -> None:
        self.command = command
        self.capture = capture
        self.override = override

    def format_event(self) -> dict:
        """
        Formats the slack event to a standard format for capture.
        """
        metadata = self.command.metadata
        #
        # adding more attributes to the metadata
        # not required for the event capture, but can be helpful for debugging
        metadata["callback_type"] = self.command.callback_type
        metadata["context_team_id"] = self.command.context_team_id
        metadata["context_enterprise_id"] = self.command.context_enterprise_id
        return {
            "event_id": self.command.event_id,
            "team_id": self.command.team_id,
            "event": self.command.event,
            "event_type": self.command.event_type,
            "event_ts": self.command.event_ts,
            "metadata": metadata,
        }

    async def _capture_with_override(self):
        event_capture_service = SlackEventCaptureService()
        event = self.format_event()
        await event_capture_service.capture(event, override=True)

    async def _capture_without_override(self):
        event_capture_service = SlackEventCaptureService()
        event = self.format_event()
        await event_capture_service.capture(event)

    async def dispatch(self):
        """
        Dispatches the Slack event to the appropriate service, based on
        the inner `type`.

        This is different from the outer `type` which is more appropriately
        can be called callback type.
        """

        team_id = self.command.team_id
        api_app_id = self.command.api_app_id

        logger.info(
            f"callback event dispatch for team_id: {team_id} and api_app_id: {api_app_id}"
        )

        if self.capture and self.override:
            await self._capture_with_override()

        if self.capture and not self.override:
            await self._capture_without_override()

        event_type = self.command.event_type
        event = self.command.event

        if event_type == "message" and "channel_type" in event:
            channel_type = event.get("channel_type")
            if channel_type == "channel":
                dispatch_key = "message.channels"
                return await self.dispatcher[dispatch_key]().execute(self.command)
            else:
                logger.error(
                    f"channel type is not a channel add supported channel type: {channel_type}"
                )
        else:
            logger.error('unsupported slack event type: "%s"', event_type)
        return await self.dispatcher["unsupported"]().execute(self.command)
