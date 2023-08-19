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
