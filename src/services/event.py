import logging
import uuid
from datetime import datetime

from src.adapters.db.adapters import SlackEventDBAdapter, TenantDBAdapter
from src.adapters.tasker import worker
from src.application.commands import SlackEventCallBackCommand
from src.application.exceptions import SlackTeamReferenceException
from src.domain.models import SlackEvent, Tenant

logger = logging.getLogger(__name__)


class SlackEventCallBackService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.slack_event_db = SlackEventDBAdapter()

    @staticmethod
    def is_ignored(event: dict) -> bool:
        inner_event: dict | None = event.get("event", None)
        if not inner_event:
            return False

        metadata: dict | None = inner_event.get("metadata", None)
        if not metadata:
            return False

        event_payload: dict | None = metadata.get("event_payload", None)
        if not event_payload:
            return False
        is_ignored: bool | None = event_payload.get("is_ignored", None)

        return is_ignored

    async def _capture(self, slack_event: SlackEvent) -> SlackEvent:
        slack_event = await self.slack_event_db.save(slack_event)
        logger.info('captured slack event: "%s"', slack_event)
        return slack_event

    async def _dispatch(self, tenant: Tenant, slack_event: SlackEvent) -> None:
        now = datetime.utcnow()
        dispatch_id = str(uuid.uuid4())
        context = {
            "dispatch_id": dispatch_id,
            "dispatched_at": now.isoformat(),
            "tenant": tenant.to_dict(),
        }

        logger.info(
            "dispatching slack event to `slack_event_dispatch_handler` "
            f"with dispatch_id: {dispatch_id} at {now.isoformat()}"
        )

        task = worker.apply_async(
            "zyg.slack_event_handler", (context, slack_event.to_dict())
        )
        logger.info("invoked task with task id: %s", task)
        return dispatch_id

    async def dispatch(self, command: SlackEventCallBackCommand) -> SlackEvent:
        """
        dispatches and captures a slack event for async event handling.

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
            raise SlackTeamReferenceException(
                f"tenant not found for `slack_team_ref`: {slack_team_ref} "
                + "may not be mapped to a tenant or is invalid."
            )

        slack_event = SlackEvent.from_payload(
            tenant_id=tenant.tenant_id, event_id=None, payload=command.payload
        )

        captured_event = await self.slack_event_db.find_by_slack_event_ref(
            command.slack_event_ref
        )

        if captured_event and captured_event.equals_by_slack_event_ref(slack_event):
            logger.warning(
                'slack event already captured: "%s" checking if acknowledged...',
                captured_event,
            )
            if not captured_event.is_ack:
                logger.warning(
                    "slack event is not acknowledged yet. Will dispatch again.",
                )
                dispatch_id = await self._dispatch(tenant, captured_event)
                logger.info(
                    'slack event dispatched again: "%s" with dispatch_id: "%s"',
                    captured_event,
                    dispatch_id,
                )
            return captured_event

        logger.info(
            'slack event not yet captured: "%s" capturing and dispatching now...',
            slack_event,
        )

        captured_event = await self._capture(slack_event)
        dispatch_id = await self._dispatch(tenant, captured_event)
        logger.info(
            'slack event captured: "%s" and dispatched with dispatch_id: "%s"',
            captured_event,
            dispatch_id,
        )

        return captured_event
