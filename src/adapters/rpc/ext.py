from typing import List

from pydantic import BaseModel, ConfigDict
from slack_sdk import WebClient

from src.domain.models import InSyncSlackChannelItem, Tenant
from src.logger import logger

from .exceptions import SlackAPIException, SlackAPIResponseException


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
    pending_connected_team_ids: list[str] = []
    pending_shared: list[str] = []
    previous_names: list[str] = []
    purpose: dict | None = None
    shared_team_ids: list[str] = []
    topic: dict | None = None
    unlinked: int | None = None
    updated: int


class SlackWebAPIConnector:
    def __init__(self, tenant: Tenant, token: str) -> None:
        self.tenant = tenant
        self.token = token
        self._client = WebClient(token=token)

    @classmethod
    def for_tenant(cls, tenant: Tenant, token: str) -> "SlackWebAPIConnector":
        # TODO: later token will be fetched from the tenant context.
        return cls(tenant=tenant, token=token)
        # return cls(tenant=tenant, token=tenant.slack_bot_oauth_token)

    def get_conversation_list(
        self, types: str = "public_channels"
    ) -> List[InSyncSlackChannelItem]:
        """
        refer the Slack API docs for more information at:
        https://api.slack.com/methods/conversations.list

        :param types: comma separated list of types to include in the response
        :return: list of InSyncSlackChannelItem
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
                conversation_item_response = SlackConversationItemResponse(**channel)
                conversation_item_response_dict = (
                    conversation_item_response.model_dump()
                )
                insync_channel_item = InSyncSlackChannelItem.from_dict(
                    self.tenant.tenant_id, data=conversation_item_response_dict
                )
                results.append(insync_channel_item)
        else:
            error = response.get("error", "unknown")
            logger.error(
                f"slack connector API error with slack error code: {error} ",
                f"check Slack docs for more information for error: {error}",
            )
            raise SlackAPIResponseException(
                f"slack connector API error with slack error code: {error}"
            )
        return results
