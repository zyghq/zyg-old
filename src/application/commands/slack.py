from typing import Any, Dict, List

from pydantic import BaseModel, constr


class ChatPostMessageCommand(BaseModel):
    channel: constr(min_length=3, to_upper=True)
    text: str
    blocks: List[Dict[str, Any]] | None = None


class NudgePostMessageCommand(ChatPostMessageCommand):
    slack_user_ref: constr(min_length=3, to_upper=True)


class ReplyPostMessageCommand(ChatPostMessageCommand):
    thread_ts: str


class GetUsersCommand(BaseModel):
    limit: int


class GetChannelsCommand(BaseModel):
    types: str = "public_channel"


class GetSingleChannelMessageCommand(BaseModel):
    channel: constr(min_length=3, to_upper=True)
    limit: int = 1
    oldest: str
    inclusive: bool | None = True


class UpdateMessageCommand(BaseModel):
    channel: constr(min_length=3, to_upper=True)
    ts: str
    text: str
    blocks: List[Dict[str, Any]] | None = None
