from datetime import datetime

from pydantic import BaseModel


class DBEntity(BaseModel):
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp


class TenantDBEntity(DBEntity):
    tenant_id: str | None = None  # primary key
    name: str
    slack_team_ref: str | None = None


class SlackEventDBEntity(DBEntity):
    event_id: str | None = None  # primary key
    tenant_id: str
    slack_event_ref: str
    inner_event_type: str | None = None
    event: dict
    event_ts: int
    api_app_id: str
    token: str
    payload: dict
    is_ack: bool = False


class InSyncSlackChannelDBEntity(DBEntity):
    tenant_id: str
    context_team_id: str
    created: int
    creator: str
    id: str
    is_archived: bool
    is_channel: bool
    is_ext_shared: bool
    is_general: bool
    is_group: bool
    is_im: bool
    is_member: bool
    is_mpim: bool
    is_org_shared: bool
    is_pending_ext_shared: bool
    is_private: bool
    is_shared: bool
    name: str
    name_normalized: str
    num_members: int
    parent_conversation: str | None = None
    pending_connected_team_ids: list[str] | None = None
    pending_shared: list[str] | None = None
    previous_names: list[str] | None = None
    purpose: dict | None = None
    shared_team_ids: list[str] | None = None
    topic: dict | None = None
    unlinked: int | None = None
    updated: int
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp


class LinkedSlackChannelDBEntity(DBEntity):
    tenant_id: str
    linked_slack_channel_id: str | None = None  # primary key
    slack_channel_ref: str
    slack_channel_name: str | None = None
    triage_slack_channel_ref: str
    triage_slack_channel_name: str | None = None
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp
