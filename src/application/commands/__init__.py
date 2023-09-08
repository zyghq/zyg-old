from pydantic import BaseModel, constr


class TenantProvisionCommand(BaseModel):
    name: str
    slack_team_ref: constr(min_length=3, max_length=255, to_lower=True)


class SlackEventCallBackCommand(BaseModel):
    slack_event_ref: constr(min_length=3, max_length=255, to_lower=True)
    slack_team_ref: constr(min_length=3, max_length=255, to_lower=True)
    event: dict
    event_ts: int
    payload: dict


class TenantSyncChannelCommand(BaseModel):
    tenant_id: str
    types: list[str] | None = None


class LinkSlackChannelCommand(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
    triage_slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
