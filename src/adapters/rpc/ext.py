import logging
from typing import List

from pydantic import BaseModel, ConfigDict
from slack_sdk import WebClient
from slack_sdk.errors import SlackClientError

from src.application.commands.slack import (
    GetChannelsCommand,
    GetSingleChannelMessage,
    GetUsersCommand,
    IssueChatPostMessageCommand,
    NudgeChatPostMessageCommand,
)
from src.domain.models import (
    InSyncSlackChannel,
    InSyncSlackUser,
    SlackChannelMessageAPIValue,
    TenantContext,
)

from .exceptions import SlackAPIException, SlackAPIResponseException

logger = logging.getLogger(__name__)


class SlackChannelItemResponse(BaseModel):
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


class SlackChannelMessageItemResponse(BaseModel):
    client_msg_id: str
    type: str
    text: str
    user: str
    ts: str
    blocks: List[dict] | None = None
    team: str
    reactions: List[dict] | None = None


class SlackWebAPI:
    def __init__(self, token: str) -> None:
        self._client = WebClient(token=token)

    def chat_post_message(self, channel, text, blocks):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/chat.postMessage
        """
        logger.info(f"invoked `chat_post_message` with args: {channel}")
        try:
            response = self._client.chat_postMessage(
                channel=channel, text=text, blocks=blocks
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def users_list(self, limit=200):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/users.list

        """
        logger.info(f"invoked `users_list` with args: {limit}")
        try:
            response = self._client.users_list(limit=limit)
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def chat_post_ephemeral(self, channel, user, text, blocks):
        logger.info(f"invoked `chat_post_ephemeral` for args: {channel, user}")
        try:
            response = self._client.chat_postEphemeral(
                channel=channel, user=user, text=text, blocks=blocks
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def conversation_list(self, types: str = "public_channels"):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/conversations.list

        :param types: comma separated list of types to include in the response
        """
        logger.info(f"invoked `conversation_list` for args: {types}")
        try:
            response = self._client.conversations_list(types=types)
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response

    def conversation_history(
        self,
        channel: str,
        inclusive: bool | None = None,
        limit: int | None = None,
        oldest: str | None = None,
    ):
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/conversations.history

        """
        logger.info(
            "invoked `conversation_history` "
            + f"for args: {channel, inclusive, limit, oldest}"
        )
        try:
            response = self._client.conversations_history(
                channel=channel, oldest=oldest, limit=limit, inclusive=inclusive
            )
        except SlackClientError as err:
            logger.error(f"slack client error: {err}")
            raise SlackAPIException("slack client error") from err

        if not response.get("ok", False):
            error = response.get("error", "unknown")
            logger.error(
                f"slack response error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack response error with slack error code: {error}"
            )
        return response


# TODO:
# @sanchitrk - API wrapper is pretty basic at the moment, we need to
# handle more use cases like pagination, rate limiting, etc.
#
# XXX: adding just random doc link for pagination inspiration
# https://github.com/slackapi/python-slack-sdk/blob/ff073cf74994adc6022e8296e702012ef5b662b4/slack/web/slack_response.py#L24-L41
class SlackWebAPIConnector(SlackWebAPI):
    def __init__(self, tenant_context: TenantContext, token: str) -> None:
        self.tenant_context = tenant_context  # TODO: raad token later from here.
        super().__init__(token=token)

    def get_channels(self, command: GetChannelsCommand) -> List[InSyncSlackChannel]:
        result = self.conversation_list(types=command.types)
        channels = result.get("channels", [])
        items = []
        for channel in channels:
            item = SlackChannelItemResponse(**channel)
            item_dict = item.model_dump()
            insync_channel = InSyncSlackChannel.from_dict(
                self.tenant_context.tenant_id, data=item_dict
            )
            items.append(insync_channel)
        return items

    # TODO: handle response from slack
    def post_issue_message(self, command: IssueChatPostMessageCommand):
        return self.chat_post_message(
            channel=command.channel, text=command.text, blocks=command.blocks
        )

    def get_users(self, command: GetUsersCommand) -> List[InSyncSlackUser]:
        result = self.users_list(limit=command.limit)
        members = result.get("members", [])
        members = list(filter(lambda d: d["deleted"] is False, members))
        users = []
        for member in members:
            item = SlackUserItemResponse(**member)
            item_dict = item.model_dump()
            insync_user = InSyncSlackUser.from_dict(
                self.tenant_context.tenant_id, data=item_dict
            )
            users.append(insync_user)
        return users

    # TODO: handle response from slack
    def nudge_for_issue(self, command: NudgeChatPostMessageCommand):
        return self.chat_post_ephemeral(
            channel=command.channel,
            user=command.slack_user_ref,
            text=command.text,
            blocks=command.blocks,
        )

    def get_single_channel_message(
        self, command: GetSingleChannelMessage
    ) -> SlackChannelMessageAPIValue | None:
        result = self.conversation_history(
            channel=command.channel,
            inclusive=command.inclusive,
            limit=command.limit,
            oldest=command.oldest,
        )
        messages = result.get("messages", [])
        if len(messages) == 0:
            return None
        message = messages[0]
        item = SlackChannelMessageItemResponse(**message)
        item_dict = item.model_dump()
        value = SlackChannelMessageAPIValue.from_dict(
            tenant_id=self.tenant_context.tenant_id, data=item_dict
        )
        return value
