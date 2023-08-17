from datetime import datetime

from pydantic import BaseModel


class SlackEventEntity(BaseModel):
    event_id: str
    token: str
    team_id: str
    api_app_id: str
    event: dict | None = None
    type: str
    event_context: str
    event_time: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_ack: bool = False
