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
