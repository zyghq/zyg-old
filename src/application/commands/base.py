from typing import List, Optional

from pydantic import BaseModel, constr, validator


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
    types: List[str] | None = None


class LinkSlackChannelCommand(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
    triage_slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)


class SearchLinkedSlackChannelCommand(BaseModel):
    tenant_id: str
    linked_slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None
    slack_channel_ref: Optional[str] = None

    @validator("slack_channel_ref")
    def to_lower(cls, v: str | None):
        return v.lower() if v else v


class CreateIssueCommand(BaseModel):
    tenant_id: str
    body: str
    status: str | None
    priority: int | None
    tags: List[str] = []
    linked_slack_channel_id: str | None = None


class GetLinkedSlackChannelByRefCommand(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
