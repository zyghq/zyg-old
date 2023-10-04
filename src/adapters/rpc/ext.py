import logging
from typing import List

from pydantic import BaseModel, ConfigDict
from slack_sdk import WebClient

from src.application.commands.slack import IssueChatPostMessageCommand
from src.domain.models import InSyncSlackChannel, InSyncSlackUser, TenantContext

from .exceptions import SlackAPIException, SlackAPIResponseException

logger = logging.getLogger(__name__)


class SlackConversationItemResponse(BaseModel):
    """
    Mapped as per the response from Slack APIs for `conversations.list`

    subject to change as per the Slack API response
    """

    model_config: ConfigDict = ConfigDict(str_to_lower=True)

    context_team_id: str
    created: int
    creator: str
    id: str
    is_archived: bool
    is_channel: bool
    is_ext_shared: bool
    is_general: bool
    is_group: bool
    is_im: bool
    is_member: bool
    is_mpim: bool
    is_org_shared: bool
    is_pending_ext_shared: bool
    is_private: bool
    is_shared: bool
    name: str
    name_normalized: str
    num_members: int
    parent_conversation: str | None = None
    pending_connected_team_ids: List[str] = []
    pending_shared: List[str] = []
    previous_names: List[str] = []
    purpose: dict | None = None
    shared_team_ids: List[str] = []
    topic: dict | None = None
    unlinked: int | None = None
    updated: int


class SlackUserItemResponse(BaseModel):
    model_config = ConfigDict(str_to_lower=True)
    id: str
    team_id: str
    name: str
    deleted: bool
    color: str
    real_name: str
    tz: str
    tz_label: str
    tz_offset: int
    profile: dict
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    is_bot: bool
    is_app_user: bool
    updated: int
    is_email_confirmed: bool
    who_can_share_contact_card: str


# TODO:
# @sanchitrk - API wrapper is pretty basic at the moment, we need to
# handle more use cases like pagination, rate limiting, etc.
#
# XXX: adding just random doc link for pagination inspiration
# https://github.com/slackapi/python-slack-sdk/blob/ff073cf74994adc6022e8296e702012ef5b662b4/slack/web/slack_response.py#L24-L41
class SlackWebAPIConnector:
    def __init__(self, tenant_context: TenantContext, token: str) -> None:
        self.tenant_context = tenant_context
        self.token = token
        self._client = WebClient(token=token)

    # TODO: rename this as private
    # create a public method which aligns with the business use case
    def get_conversation_list(
        self, types: str = "public_channels"
    ) -> List[InSyncSlackChannel]:
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/conversations.list

        :param types: comma separated list of types to include in the response
        :return: list of InSyncSlackChannel
        """
        logger.info(f"invoked `get_conversation_list` for args: {types}")
        try:
            response = self._client.conversations_list(types=types)
        except SlackAPIException as e:
            logger.error(f"slack API error: {e}")

        logger.info("slack got response!")
        results = []
        if response.get("ok"):
            for channel in response.get("channels", []):
                item = SlackConversationItemResponse(**channel)
                item_dict = item.model_dump()
                insync_channel = InSyncSlackChannel.from_dict(
                    self.tenant_context.tenant_id, data=item_dict
                )
                results.append(insync_channel)
        else:
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return results

    def _chat_post_message(self, channel, text, blocks):
        logger.info(f"invoked `chat_post_message` for args: {channel}")
        try:
            response = self._client.chat_postMessage(
                channel=channel, text=text, blocks=blocks
            )
        except SlackAPIException as e:
            logger.error(f"slack API error: {e}")

        logger.info("slack got response!")
        if response.get("ok"):
            return response
        else:
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )

    def post_issue_message(self, command: IssueChatPostMessageCommand):
        return self._chat_post_message(
            channel=command.channel, text=command.text, blocks=command.blocks
        )

    # TODO: @sanchitrk - for now keep it simple we'll tweak it later
    # once we have better understanding of how to deal with pagination.
    def _users_list(self, limit=200):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/users.list

        """
        try:
            response = self._client.users_list(limit=limit)
        except SlackAPIException as e:
            logger.error(f"slack API error: {e}")

        logger.info("slack got response!")
        results = []
        if response.get("ok"):
            for user in response.get("members", []):
                results.append(user)
        else:
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return results

    # TODO: @sanchitrk - update this later to take `command` as input
    def get_users(self, limit) -> List[InSyncSlackUser]:
        results = self._users_list(limit=limit)
        results = list(filter(lambda d: d["deleted"] is False, results))
        users = []
        for result in results:
            item = SlackUserItemResponse(**result)
            item_dict = item.model_dump()
            insync_user = InSyncSlackUser.from_dict(
                self.tenant_context.tenant_id, data=item_dict
            )
            users.append(insync_user)
        return users
