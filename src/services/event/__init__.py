from src.adapters.db.adapters import SlackEventDBAdapter, TenantDBAdapter
from src.application.commands import SlackEventCallBackCommand
from src.application.exceptions import SlackTeamRefMapException
from src.domain.models import SlackEvent
from src.logger import logger


class SlackEventCallBackDispatchService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.slack_event_db = SlackEventDBAdapter()

    async def _capture(self, slack_event: SlackEvent) -> None:
        slack_event = await self.slack_event_db.save(slack_event)
        logger.info('captured slack event: "%s"', slack_event)
        return slack_event

    async def _dispatch(self, slack_event: SlackEvent) -> None:
        raise NotImplementedError

    async def dispatch(self, command: SlackEventCallBackCommand) -> SlackEvent:
        """
        dispatches and captures a slack event to messagebus for async event handling.

        We check if the event has already been captured by comparing the
        `slack_event_ref`

        `slack_event_ref` is globally unique across all tenants
        (according to Slack API docs)

        Note:
            We can do a lot more here, like checking if the `slack_event_ref` and
            `event_id` are the same, but for now, we'll just check the `slack_event_ref`
            since it's globally unique.

            Also, we can check if the event has already been processed by checking
            the `is_ack` flag, but we'll leave that for now.

        Args:
            command (SlackEventCallBackCommand): The command object.
        """
        slack_team_ref = command.slack_team_ref
        tenant = await self.tenant_db.find_by_slack_team_ref(slack_team_ref)
        if not tenant:
            raise SlackTeamRefMapException(
                f"tenant not found. `slack_team_ref`: {slack_team_ref} "
                + "is not mapped to a tenant or is invalid."
            )

        slack_event = SlackEvent.from_payload(
            tenant_id=tenant.tenant_id, payload=command.payload
        )

        captured_slack_event = await self.slack_event_db.find_by_slack_event_ref(
            command.slack_event_ref
        )

        if captured_slack_event.equals_by_slack_event_ref(slack_event):
            logger.warning(
                'slack event already captured: "%s" skipping dispatch.',
                captured_slack_event,
            )
            return captured_slack_event

        slack_event_captured = await self._capture(slack_event)
        return slack_event_captured
