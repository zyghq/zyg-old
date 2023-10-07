from typing import Any, Dict, List

from pydantic import BaseModel, constr


class IssueChatPostMessageCommand(BaseModel):
    channel: constr(min_length=3, to_upper=True)
    text: str
    blocks: List[Dict[str, Any]] | None = None


class NudgeChatPostMessageCommand(BaseModel):
    channel: constr(min_length=3, to_upper=True)
    slack_user_ref: constr(min_length=3, to_upper=True)
    text: str
    blocks: List[Dict[str, Any]] | None = None


class GetUsersCommand(BaseModel):
    limit: int


class GetChannelsCommand(BaseModel):
    types: str = "public_channel"


class GetSingleChannelMessage(BaseModel):
    channel: constr(min_length=3, to_upper=True)
    limit: int = 1
    oldest: str
    inclusive: bool | None = True


# {
#     "client_msg_id": "7924c1bd-2af2-4e81-a25c-c4d60533739c",
#     "type": "message",
#     "text": "No matter what numbers I enter, the calculator always gives me the wrong answer for division. I have tried restarting the app and my phone, but the problem persists. sent at 8.52 source message - will add reaction to it later time.",
#     "user": "U03NGJTT5JT",
#     "ts": "1696562588.349219",
#     "blocks": [
#         {
#             "type": "rich_text",
#             "block_id": "sVAI",
#             "elements": [
#                 {
#                     "type": "rich_text_section",
#                     "elements": [
#                         {
#                             "type": "text",
#                             "text": "No matter what numbers I enter, the calculator always gives me the wrong answer for division. I have tried restarting the app and my phone, but the problem persists. sent at 8.52 source message - will add reaction to it later time.",
#                         }
#                     ],
#                 }
#             ],
#         }
#     ],
#     "team": "T03NX4VMCRH",
#     "reactions": [{"name": "ticket", "users": ["U03NGJTT5JT"], "count": 1}],
# }
