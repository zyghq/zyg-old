from pydantic import BaseModel
from src.domain.models import SlackEvent


class TenantRepr(BaseModel):
    name: str
    tenant_id: str
    slack_team_ref: str


class SlackCallBackEventRepr(BaseModel):
    pass


def slack_callback_event_repr_factory(
    slack_event: SlackEvent,
) -> SlackCallBackEventRepr:
    pass
