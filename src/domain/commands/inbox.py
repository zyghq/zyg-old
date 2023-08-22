from pydantic import BaseModel


class CreateInboxCommand(BaseModel):
    name: str
    description: str
    slack_channel_id: str | None = None
