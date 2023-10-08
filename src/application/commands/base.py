from typing import List, Optional

from pydantic import BaseModel, constr, validator


class TenantProvisionCommand(BaseModel):
    name: str
    slack_team_ref: constr(min_length=3, max_length=255, to_lower=True)


class SlackEventCallBackCommand(BaseModel):
    slack_event_ref: constr(min_length=3, max_length=255, to_lower=True)
    slack_team_ref: constr(min_length=3, max_length=255, to_lower=True)
    event: dict
    event_dispatched_ts: int
    payload: dict


class TenantSyncChannelCommand(BaseModel):
    tenant_id: str
    types: List[str] | None = None


class SlackSyncUserCommand(BaseModel):
    tenant_id: str
    upsert_user: bool = False


class LinkSlackChannelCommand(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
    triage_slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)


class SearchSlackChannelCommand(BaseModel):
    tenant_id: str
    slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None
    slack_channel_ref: Optional[str] = None

    @validator("slack_channel_ref")
    def to_lower(cls, v: str | None):
        return v.lower() if v else v


class SearchUserCommand(BaseModel):
    tenant_id: str
    user_id: Optional[str] = None
    slack_user_ref: Optional[str] = None

    @validator("slack_user_ref")
    def to_lower(cls, v: str | None):
        return v.lower() if v else v


class CreateIssueCommand(BaseModel):
    tenant_id: str
    body: str
    status: str | None
    priority: int | None
    tags: List[str] = []
    slack_channel_id: str | None = None


class GetLinkedSlackChannelByRefCommand(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)


class GetUserByRefCommand(BaseModel):
    tenant_id: str
    slack_user_ref: constr(min_length=3, max_length=255, to_lower=True)
