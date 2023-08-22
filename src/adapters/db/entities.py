from datetime import datetime

from pydantic import BaseModel


class SlackEventDbEntity(BaseModel):
    event_id: str  # primary key
    team_id: str
    event: dict | None = None
    event_type: str
    event_ts: int
    metadata: dict | None = None
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp
    is_ack: bool = False


class InboxDbEntity(BaseModel):
    inbox_id: str  # primary key
    name: str
    description: str | None = None
    slack_channel_id: str | None = None
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp


class SlackChannelDBEntity(BaseModel):
    channel_id: str  # primary key
    name: str
    channel_type: str
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp
