import logging
from typing import Callable

from src.adapters.rpc.api import ZygWebAPIConnector
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import CreateIssueCommand
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import Issue, SlackEvent, Tenant
from src.services.exceptions import UnSupportedSlackEventException

logger = logging.getLogger(__name__)


# text = "There is an issue in login for android app!!"

# test_block = issue_template = {
#     "blocks": [
#         {
#             "type": "section",
#             "text": {
#                 "type": "plain_text",
#                 "text": ":red_circle: Awaiting",
#                 "emoji": True,
#             },
#         },
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": ":ticket: <https://example.com|*Issue #1789*>",
#             },
#         },
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": "_<@U03NGJTT5JT> In <#C05KPPM03T8> | 9 Sept 2023 at 11:08 AM_",
#             },
#         },
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": "There is an issue in login for android app!!",
#             },
#         },
#         {"type": "divider"},
#         {
#             "type": "context",
#             "elements": [
#                 {"type": "mrkdwn", "text": "Requester: *<@U03NGJTT5JT>*"},
#                 {"type": "mrkdwn", "text": "*Unassigned*"},
#                 {"type": "mrkdwn", "text": "Priority: *Normal*"},
#             ],
#         },
#         {
#             "type": "actions",
#             "elements": [
#                 {
#                     "type": "button",
#                     "text": {"type": "plain_text", "text": "Claim", "emoji": True},
#                     "style": "primary",
#                     "value": "click_me_123",
#                     "action_id": "actionId-0",
#                 }
#             ],
#         },
#     ]
# }


class CreateIssueWithSlackTask:
    def __init__(self) -> None:
        pass

    async def create(self, tenant: Tenant, slack_event: SlackEvent):
        logger.info(f"create issue for tenant: {tenant}")
        tenant_context = tenant.build_context()
        message = slack_event.get_message()

        if message:
            body = message.get("body")

        # slack_api = SlackWebAPIConnector.for_tenant(
        #     tenant_context=tenant_context,
        #     token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        # )

        # response = slack_api.chat_post_message(
        #     channel="C05LB4YTKK8",
        #     text=text,
        #     blocks=test_block["blocks"],
        # )

        command = CreateIssueCommand(
            tenant_id=tenant_context.tenant_id,
            body=body,
            status=Issue.default_status(),
            priority=Issue.default_priority(),
            tags=[],
        )

        api = ZygWebAPIConnector(tenant_context=tenant_context)
        err, response = await api.create_issue(command=command)
        if err:
            logger.error(f"error: {err}")
            return None
        logger.info(f"slack got response: {response}")


async def slack_channel_message_handler(tenant: Tenant, slack_event: SlackEvent):
    logger.info("slack_channel_message_handler invoked")
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
