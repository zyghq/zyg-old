import logging
from typing import Callable

from src.adapters.rpc.api import ZygWebAPIConnector
from src.adapters.rpc.exceptions import UserNotFoundAPIError
from src.adapters.rpc.ext.slack import SlackWebAPIConnector
from src.application.commands.api import (
    CreateIssueAPICommand,
    FindIssueBySlackChannelIdMessageTsAPICommand,
    FindSlackChannelByRefAPICommand,
    FindUserByRefAPICommand,
)
from src.application.commands.slack import (
    ChatPostMessageCommand,
    GetSingleChannelMessageCommand,
    NudgePostMessageCommand,
    ReplyPostMessageCommand,
)
from src.application.repr.slack import (
    issue_message_blocks_repr,
    issue_message_text_repr,
    issue_opened_reply_blocks_repr,
    issue_opened_reply_text_repr,
    nudge_issue_blocks_repr,
    nudge_issue_text_repr,
)
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import (
    ChannelMessage,
    Issue,
    MessageReactionAdded,
    SlackChannel,
    SlackEvent,
    Tenant,
    User,
)
from src.services.exceptions import UnSupportedSlackEventException

logger = logging.getLogger(__name__)


async def channel_message_handler(tenant: Tenant, slack_event: SlackEvent):
    """
    func named after Slack API event type: `message.channels`
    """
    logger.info("handler for slack event: `message.channels`")
    logger.info(f"tenant: {tenant}")
    logger.info(f"slack_event: {slack_event}")

    if not slack_event.is_channel_message:
        raise RuntimeError(
            "slack event is not a channel message event "
            + "this handler only supports channel message event"
        )

    event: ChannelMessage = slack_event.event
    slack_user_ref = event.slack_user_ref
    if not slack_user_ref:
        raise ValueError("`slack_user_ref` is required for channel message event")

    zyg_api = ZygWebAPIConnector(tenant_context=tenant.build_context())

    try:
        response = await zyg_api.get_user_by_slack_ref(
            command=FindUserByRefAPICommand(
                tenant_id=tenant.tenant_id,
                slack_user_ref=slack_user_ref,
            )
        )
        data = {
            "tenant_id": tenant.tenant_id,
            "user_id": response["user_id"],
            "slack_user_ref": response["slack_user_ref"],
            "name": response["name"],
            "role": response["role"],
        }
        user = User.from_dict(data)
    except UserNotFoundAPIError as e:
        logger.error(f"error: {e}")
        return None

    slack_api = SlackWebAPIConnector(
        tenant_context=tenant.build_context(),
        token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
    )

    command = NudgePostMessageCommand(
        channel=event.slack_channel_ref,
        slack_user_ref=user.slack_user_ref,
        text=nudge_issue_text_repr(user.display_name),
        blocks=nudge_issue_blocks_repr(user.display_name),
    )
    metadata = {
        "event_type": "issue_nudge",
        "event_payload": {"is_ignored": True},
    }
    response = slack_api.nudge_for_issue(command, metadata=metadata)

    print(f"response: {response}")

    return response


async def reaction_added_handler(tenant: Tenant, slack_event: SlackEvent):
    """
    func named after Slack API event type: `reaction_added`
    """
    logger.info("handler for slack event: `reaction_added`")
    logger.info(f"tenant: {tenant}")
    logger.info(f"slack_event: {slack_event}")

    if not slack_event.is_reaction_added:
        raise RuntimeError("slack event is not a reaction added event")

    event: MessageReactionAdded = slack_event.event
    if not event.is_reaction_ticket:
        logger.info("reaction is not a ticket emoji ignore and terminate")
        return None
    logger.info("reaction is a ticket emoji")

    zyg_api = ZygWebAPIConnector(tenant_context=tenant.build_context())
    slack_api = SlackWebAPIConnector(
        tenant_context=tenant.build_context(),
        token=SLACK_BOT_OAUTH_TOKEN,
    )

    logger.info("find slack channel by ref...")
    command = FindSlackChannelByRefAPICommand(
        tenant_id=tenant.tenant_id,
        slack_channel_ref=event.slack_channel_ref,
    )

    result = await zyg_api.find_slack_channel_by_ref(command)
    if not result:
        logger.warning("slack channel not found or is not linked to track for issue")
        return None
    slack_channel = SlackChannel.from_dict(tenant.tenant_id, result[0])

    logger.info("find issue for slack channel id and message ts...")
    command = FindIssueBySlackChannelIdMessageTsAPICommand(
        tenant_id=tenant.tenant_id,
        slack_channel_id=slack_channel.slack_channel_id,
        slack_message_ts=event.message_ts,
    )

    result = await zyg_api.find_issue_by_slack_channel_id_message_ts(command)
    if result:
        logger.info("issue already exists for the slack message ignore and terminate")
        return None

    logger.info("issue not yet created for the slack message...")
    logger.info("getting slack message for added reaction...")
    command = GetSingleChannelMessageCommand(
        channel=event.slack_channel_ref,
        limit=1,
        oldest=event.message_ts,
        inclusive=True,
    )

    slack_message = slack_api.find_single_channel_message(command)
    if slack_message is None:
        logger.warning("no slack message found for the reaction added")
        return None

    logger.info("create with for the slack message...")
    command = CreateIssueAPICommand(
        tenant_id=tenant.tenant_id,
        slack_channel_id=slack_channel.slack_channel_id,
        slack_message_ts=event.message_ts,
        body=slack_message.text,
        status=Issue.default_status(),
        priority=Issue.default_priority(),
        tags=None,
    )
    result = await zyg_api.create_issue(command)
    issue = Issue.from_dict(tenant.tenant_id, result)

    logger.info("reply to the created issue...")
    command = ReplyPostMessageCommand(
        channel=event.slack_channel_ref,
        thread_ts=slack_message.ts,
        text=issue_opened_reply_text_repr(event.slack_user_ref),
        blocks=issue_opened_reply_blocks_repr(
            event.slack_user_ref, issue_number=issue.issue_number
        ),
    )
    metadata = {
        "event_type": "issue_opened",
        "event_payload": {
            "issue_id": issue.issue_id,
            "issue_number": issue.issue_number,
            "slack_channel_id": issue.slack_channel_id,
            "slack_message_ts": issue.slack_message_ts,
            "issue_status": issue.status,
            "issue_priority": issue.priority,
        },
    }
    response = slack_api.reply_to_message(command, metadata=metadata)
    return response


_SUBSCRIBED_EVENT_HANDLERS = {
    "message.channels": channel_message_handler,
    "reaction_added": reaction_added_handler,
}


def event_handler(subscribed_event) -> Callable:
    func = _SUBSCRIBED_EVENT_HANDLERS.get(subscribed_event, None)
    if func is None:
        raise UnSupportedSlackEventException(
            f"event: `{subscribed_event}` is not supported."
        )
    return func
