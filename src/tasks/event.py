import logging
from typing import Callable

from src.adapters.rpc.api import ZygWebAPIConnector
from src.adapters.rpc.exceptions import CreateIssueAPIException
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import CreateIssueCommand
from src.application.commands.slack import IssueChatPostMessageCommand
from src.application.repr.slack import (
    issue_message_blocks_repr,
    issue_message_text_repr,
)
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import Issue, SlackEvent, Tenant
from src.services.exceptions import UnSupportedSlackEventException

logger = logging.getLogger(__name__)


class CreateIssueWithSlackTask:
    def __init__(self) -> None:
        pass

    async def create(self, tenant: Tenant, slack_event: SlackEvent):
        logger.info(f"create issue for tenant: {tenant}")
        tenant_context = tenant.build_context()

        if not slack_event.is_channel_message:
            raise RuntimeError("slack_event is not channel message event")

        event = slack_event.event
        message = event.message
        body = message.get("body")

        command = CreateIssueCommand(
            tenant_id=tenant_context.tenant_id,
            body=body,
            status=Issue.default_status(),
            priority=Issue.default_priority(),
            tags=[],
        )

        zyg_api = ZygWebAPIConnector(tenant_context=tenant_context)
        try:
            response = await zyg_api.create_issue(command=command)
            issue = Issue.from_dict(response)
            logger.info(f"created issue from API {issue}")
        except CreateIssueAPIException as e:
            logger.error(f"error: {e}")
            return None

        print('************************** check the block repr ....... ')
        print(issue_message_blocks_repr(issue))
        slack_command = IssueChatPostMessageCommand(
            channel="C05LB4YTKK8",
            text=issue_message_text_repr(issue),
            blocks=issue_message_blocks_repr(issue),
        )

        slack_api = SlackWebAPIConnector(
            tenant_context=tenant_context,
            token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        )

        response = slack_api.post_issue_message(command=slack_command)
        return response


async def slack_channel_message_handler(tenant: Tenant, slack_event: SlackEvent):
    logger.info("slack_channel_message_handler invoked...")
    logger.info(f"tenant: {tenant}")
    logger.info(f"slack_event: {slack_event}")
    # print("----------------------------------")
    # print((tenant.to_dict()))
    # print("----------------------------------")
    # print(slack_event.to_dict())
    # print("----------------------------------")

    issue_task = CreateIssueWithSlackTask()
    response = await issue_task.create(tenant=tenant, slack_event=slack_event)

    return response


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
