from pydantic import BaseModel


class IssueChatPostMessageCommand(BaseModel):
    channel: str
    text: str
    blocks: None = None
