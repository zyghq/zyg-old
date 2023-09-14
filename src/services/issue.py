import logging

from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import CreateIssueWithSlackCommand
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import Tenant

logger = logging.getLogger(__name__)

text = "I am having trouble logging into the App based on OTP."

test_block = issue_template = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ":red_circle: Awaiting",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":ticket: <https://example.com|*Issue #1789*>",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_<@U03NGJTT5JT> In <#C05KPPM03T8> | 9 Sept 2023 at 11:08 AM_",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "I am having trouble logging into the App based on OTP.",
            },
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Requester: *<@U03NGJTT5JT>*"},
                {"type": "mrkdwn", "text": "*Unassigned*"},
                {"type": "mrkdwn", "text": "Priority: *Normal*"},
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Claim", "emoji": True},
                    "style": "primary",
                    "value": "click_me_123",
                    "action_id": "actionId-0",
                }
            ],
        },
    ]
}


class CreateIssueWithSlackService:
    def __init__(self) -> None:
        pass

    async def create(self, tenant: Tenant, command: CreateIssueWithSlackCommand):
        logger.info(f"create issue for tenant: {tenant} with command: {command}")

        tenant_context = tenant.build_context()
        slack_api = SlackWebAPIConnector.for_tenant(
            tenant_context=tenant_context,
            token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        )

        response = slack_api.chat_post_message(
            channel="C05LB4YTKK8",
            text=text,
            blocks=test_block["blocks"],
        )

        logger.info(f"slack got response: {response}")
