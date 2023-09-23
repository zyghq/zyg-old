import logging
from typing import Callable

from src.adapters.rpc.api import ZygWebAPIConnector
from src.adapters.rpc.exceptions import (
    CreateIssueAPIException,
    LinkedChannelRefAPIException,
)
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import (
    CreateIssueCommand,
    GetLinkedSlackChannelByRefCommand,
)
from src.application.commands.slack import IssueChatPostMessageCommand
from src.application.repr.slack import (
    issue_message_blocks_repr,
    issue_message_text_repr,
)
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import Issue, LinkedSlackChannel, SlackEvent, Tenant
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
        slack_channel_ref = event.slack_channel_ref

        zyg_api = ZygWebAPIConnector(tenant_context=tenant_context)

        try:
            response = await zyg_api.find_linked_channel_by_ref(
                command=GetLinkedSlackChannelByRefCommand(
                    tenant_id=tenant_context.tenant_id,
                    slack_channel_ref=slack_channel_ref,
                )
            )

            if response is None:
                logger.warning(
                    f"no linked slack channel found for "
                    f"slack_channel_ref: {slack_channel_ref} "
                    f"will not being creating an issue. "
                    f"consider creating the linked slack channel first "
                    "if this is the intention"
                )
                return None
            data = {
                "tenant_id": tenant_context.tenant_id,
                "linked_slack_channel_id": response["channel_id"],
                "slack_channel_ref": response["channel_ref"],
                "slack_channel_name": response["channel_name"],
                "triage_channel": {
                    "slack_channel_ref": response["triage_channel"]["channel_ref"],
                    "slack_channel_name": response["triage_channel"]["channel_name"],
                },
            }
            slack_channel = LinkedSlackChannel.from_dict(data)
            logger.info(f"linked slack channel: {slack_channel}")
        except LinkedChannelRefAPIException as e:
            logger.error(f"error: {e}")
            return None

        command = CreateIssueCommand(
            tenant_id=tenant_context.tenant_id,
            body=body,
            status=Issue.default_status(),
            priority=Issue.default_priority(),
            tags=[],
            linked_slack_channel_id=slack_channel.linked_slack_channel_id,
        )

        try:
            response = await zyg_api.create_issue(command=command)
            issue = Issue.from_dict(response)
            logger.info(f"created issue with API: {issue}")
        except CreateIssueAPIException as e:
            logger.error(f"error: {e}")
            return None

        triage_channel = slack_channel.triage_channel
        if triage_channel is None:
            logger.warning(
                "triage_channel not setup for linked_slack_channel cannot post message"
            )
            logger.warning(
                "shall we set up a default triage channel for cases like this...?"
            )
            return None
        slack_command = IssueChatPostMessageCommand(
            channel=triage_channel.slack_channel_ref,
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
