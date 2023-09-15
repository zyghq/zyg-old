import logging
from typing import Callable

from src.application.commands import CreateIssueWithSlackCommand
from src.domain.models import SlackEvent, Tenant
from src.services.exceptions import UnSupportedSlackEventException
from src.services.issue import CreateIssueWithSlackService

logger = logging.getLogger(__name__)


async def slack_channel_message_handler(tenant: Tenant, slack_event: SlackEvent):
    logger.info("slack_channel_message_handler invoked")
    logger.info(f"tenant: {tenant}")
    logger.info(f"slack_event: {slack_event}")

    command = CreateIssueWithSlackCommand()

    issue_task_service = CreateIssueWithSlackService()
    await issue_task_service.create(tenant=tenant, command=command)

    return "slack_channel_message_handler invoked"


_SUBSCRIBED_EVENT_HANDLERS = {
    "message.channels": slack_channel_message_handler,
}


def lookup_event_handler(subscribed_event) -> Callable:
    func = _SUBSCRIBED_EVENT_HANDLERS.get(subscribed_event, None)
    if func is None:
        raise UnSupportedSlackEventException(
            f"event: `{subscribed_event}` is not supported."
        )
    return func
