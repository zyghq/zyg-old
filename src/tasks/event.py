import logging
from typing import Callable

from src.adapters.rpc.api import ZygWebAPIConnector
from src.adapters.rpc.exceptions import (
    CreateIssueAPIException,
    LinkedChannelAPIException,
    UserAPIException,
)
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import (
    CreateIssueCommand,
    GetLinkedSlackChannelByRefCommand,
    GetUserByRefCommand,
)
from src.application.commands.slack import (
    IssueChatPostMessageCommand,
    NudgeChatPostMessageCommand,
)
from src.application.repr.slack import (
    issue_message_blocks_repr,
    issue_message_text_repr,
    nudge_issue_message_blocks_repr,
    nudge_issue_message_text_repr,
)
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import Issue, LinkedSlackChannel, SlackEvent, Tenant, User
from src.services.exceptions import UnSupportedSlackEventException

logger = logging.getLogger(__name__)


# class CreateIssueWithSlackTask:
#     def __init__(self) -> None:
#         pass

#     async def create(self, tenant: Tenant, slack_event: SlackEvent):
#         logger.info(f"create issue for tenant: {tenant}")
#         tenant_context = tenant.build_context()

#         if not slack_event.is_channel_message:
#             raise RuntimeError("slack_event is not channel message event")

#         event = slack_event.event
#         message = event.message
#         body = message.get("body")  # TODO: make it property rather than being dict.
#         slack_channel_ref = event.slack_channel_ref

#         zyg_api = ZygWebAPIConnector(tenant_context=tenant_context)

#         try:
#             response = await zyg_api.find_linked_channel_by_ref(
#                 command=GetLinkedSlackChannelByRefCommand(
#                     tenant_id=tenant_context.tenant_id,
#                     slack_channel_ref=slack_channel_ref,
#                 )
#             )

#             if response is None:
#                 logger.warning(
#                     f"no linked slack channel found for "
#                     f"slack_channel_ref: {slack_channel_ref} "
#                     f"will not being creating an issue. "
#                     f"consider creating the linked slack channel first "
#                     "if this is the intention"
#                 )
#                 return None
#             data = {
#                 "tenant_id": tenant_context.tenant_id,
#                 "linked_slack_channel_id": response["channel_id"],
#                 "slack_channel_ref": response["channel_ref"],
#                 "slack_channel_name": response["channel_name"],
#                 "triage_channel": {
#                     "slack_channel_ref": response["triage_channel"]["channel_ref"],
#                     "slack_channel_name": response["triage_channel"]["channel_name"],
#                 },
#             }
#             slack_channel = LinkedSlackChannel.from_dict(data)
#             logger.info(f"linked slack channel: {slack_channel}")
#         except LinkedChannelAPIException as e:
#             logger.error(f"error: {e}")
#             return None

#         command = CreateIssueCommand(
#             tenant_id=tenant_context.tenant_id,
#             body=body,
#             status=Issue.default_status(),
#             priority=Issue.default_priority(),
#             tags=[],
#             linked_slack_channel_id=slack_channel.linked_slack_channel_id,
#         )

#         try:
#             response = await zyg_api.create_issue(command=command)
#             issue = Issue.from_dict(response)
#             logger.info(f"created issue with API: {issue}")
#         except CreateIssueAPIException as e:
#             logger.error(f"error: {e}")
#             return None

#         triage_channel = slack_channel.triage_channel
#         if triage_channel is None:
#             logger.warning(
#                 "triage_channel not setup for linked_slack_channel cannot post message"
#             )
#             logger.warning(
#                 "shall we set up a default triage channel for cases like this...?"
#             )
#             return None
#         slack_command = IssueChatPostMessageCommand(
#             channel=triage_channel.slack_channel_ref,
#             text=issue_message_text_repr(issue),
#             blocks=issue_message_blocks_repr(issue),
#         )

#         slack_api = SlackWebAPIConnector(
#             tenant_context=tenant_context,
#             token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
#         )

#         response = slack_api.post_issue_message(command=slack_command)
#         return response


async def _nudge_user_for_issue():
    pass


# async def slack_channel_message_handler(tenant: Tenant, slack_event: SlackEvent):
#     """
#     func named after Slack API event type: `message.channels`
#     """
#     logger.info("slack_channel_message_handler invoked...")
#     logger.info(f"tenant: {tenant}")
#     logger.info(f"slack_event: {slack_event}")
#     # print("----------------------------------")
#     # print((tenant.to_dict()))
#     # print("----------------------------------")
#     # print(slack_event.to_dict())
#     # print("----------------------------------")

#     issue_task = CreateIssueWithSlackTask()
#     response = await issue_task.create(tenant=tenant, slack_event=slack_event)

#     return response


async def channel_message_handler(tenant: Tenant, slack_event: SlackEvent):
    """
    func named after Slack API event type: `message.channels`
    """
    logger.info("handler for slack event: `message.channels`")
    logger.info(f"tenant: {tenant}")
    logger.info(f"slack_event: {slack_event}")

    if not slack_event.is_channel_message:
        raise RuntimeError("slack event is not a channel message event")

    event = slack_event.event
    slack_user_ref = event.slack_user_ref

    if not slack_user_ref:
        raise TypeError("slack_user_ref cannot be None for channel message event")

    zyg_api = ZygWebAPIConnector(tenant_context=tenant.build_context())

    try:
        response = await zyg_api.find_user_by_slack_ref(
            command=GetUserByRefCommand(
                tenant_id=tenant.tenant_id,
                slack_user_ref=slack_user_ref,
            )
        )
        if response is None:
            logger.warning(f"no user found for slack_user_ref: {slack_user_ref}")
            return None

        data = {
            "tenant_id": tenant.tenant_id,
            "user_id": response["user_id"],
            "slack_user_ref": response["slack_user_ref"],
            "name": response["name"],
            "role": response["role"],
        }
        user = User.from_dict(data)
    except UserAPIException as e:
        logger.error(f"error: {e}")
        return None

    # print("*********** DATA REQUIRED FOR SENDING THE NUDGE **************")
    # print(f"user: {user}")
    # print("**************")
    # print(f"tenant: {tenant}")
    # print("**************")
    # print(f"slack_event: {slack_event}")
    # print("*********** DATA REQUIRED FOR SENDING THE NUDGE **************")

    slack_api = SlackWebAPIConnector(
        tenant_context=tenant.build_context(),
        token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
    )

    nudge_for_issue_command = NudgeChatPostMessageCommand(
        channel=event.slack_channel_ref,
        slack_user_ref=user.slack_user_ref,
        text=nudge_issue_message_text_repr(user.display_name),
        blocks=nudge_issue_message_blocks_repr(user.display_name),
    )

    response = slack_api.nudge_for_issue(nudge_for_issue_command)

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
    
    event = slack_event.event

    print("******************* reaction added event hurray *******************")
    print(event)
    return None


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
