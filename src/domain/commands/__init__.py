from pydantic import BaseModel


class SlackEventCommand(BaseModel):
    event_id: str
    team_id: str
    api_app_id: str
    event: dict
    event_type: str
    event_ts: int
    callback_type: str
    context_team_id: str | None = None
    context_enterprise_id: str | None = None
    metadata: dict | None = None


class CreateInboxCommand(BaseModel):
    name: str
    description: str
    slack_channel_id: str | None = None


class CreateSlackChannelCommand(BaseModel):
    channel_id: str | None
    name: str
    channel_type: str
