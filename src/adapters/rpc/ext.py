from typing import List

from pydantic import BaseModel, ConfigDict
from slack_sdk import WebClient

from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import ForSyncSlackConversationItem
from src.logger import logger

from .exceptions import SlackAPIException, SlackAPIResponseException

#
#  Sanchit Rk
#  sanchitrrk@gmail.com
#  
#  TODO:
#  for now we are reading from env, but ideally this will some how be injected
#  from the tenant context
slack_web_client = WebClient(token=SLACK_BOT_OAUTH_TOKEN)


class SlackConversationItemResponse(BaseModel):
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
    purpose: dict
    shared_team_ids: list[str] = []
    topic: dict
    unlinked: int
    updated: int


class SlackWebAPIConnector:
    def __init__(self, client: WebClient = slack_web_client) -> None:
        self.client = client

    def get_conversation_list(
        self, types: str = "public_channels"
    ) -> List[ForSyncSlackConversationItem]:
        logger.info(f"invoked `get_conversation_list` for args: {types}")
        try:
            response = self.client.conversations_list(types=types)
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
                conversation_item = ForSyncSlackConversationItem.from_dict(
                    conversation_item_response_dict
                )
                results.append(conversation_item)
        else:
            error = response.get("error", "unknown")
            logger.error(f"slack connector API error with slack error code: {error}")
            raise SlackAPIResponseException(
                f"slack connector API error with slack error code: {error}"
            )
        return results
