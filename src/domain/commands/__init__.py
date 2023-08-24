from pydantic import BaseModel


class CreateSlackEventCommand(BaseModel):
    event_id: str
    team_id: str
    event: dict
    event_type: str
    event_ts: int
    metadata: dict | None = None


class CreateInboxCommand(BaseModel):
    name: str
    description: str
    slack_channel_id: str | None = None


class CreateSlackChannelCommand(BaseModel):
    channel_id: str | None
    name: str
    channel_type: str


class CreateIssueCommand(BaseModel):
    title: str | None = None
    body: str
    requester_id: str
    slack_channel_id: str
