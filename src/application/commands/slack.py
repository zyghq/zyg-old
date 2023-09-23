from typing import Any, Dict, List

from pydantic import BaseModel


class IssueChatPostMessageCommand(BaseModel):
    channel: str
    text: str
    blocks: List[Dict[str, Any]] | None = None
