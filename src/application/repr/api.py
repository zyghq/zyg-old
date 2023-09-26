from datetime import datetime
from typing import List

from pydantic import BaseModel

from src.domain.models import (
    InSyncSlackChannel,
    InSyncSlackUser,
    Issue,
    LinkedSlackChannel,
    SlackEvent,
)


class TenantRepr(BaseModel):
    name: str
    tenant_id: str
    slack_team_ref: str


class SlackCallBackEventRepr(BaseModel):
    event_id: str
    is_ack: bool


class InSyncSlackChannelRepr(BaseModel):
    id: str
    name: str
    created: int
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
    topic: dict
    updated: int
    updated_at: datetime
    created_at: datetime


class InSyncSlackUserRepr(BaseModel):
    id: str
    name: str
    is_bot: bool
    updated_at: datetime
    created_at: datetime


class TriageSlackChannelRepr(BaseModel):
    channel_ref: str
    channel_name: str


class LinkedSlackChannelRepr(BaseModel):
    channel_id: str
    channel_ref: str
    channel_name: str
    triage_channel: TriageSlackChannelRepr


class IssueRepr(BaseModel):
    tenant_id: str
    issue_id: str
    issue_number: int
    body: str
    status: str
    priority: int
    tags: List[str] = []
    linked_slack_channel_id: str | None = None


def slack_callback_event_repr(
    slack_event: SlackEvent,
) -> SlackCallBackEventRepr:
    return SlackCallBackEventRepr(
        event_id=slack_event.event_id,
        is_ack=slack_event.is_ack,
    )


def insync_slack_channel_repr(
    item: InSyncSlackChannel,
) -> InSyncSlackChannelRepr:
    topic = {
        "value": item.topic.get("value", ""),
    }
    return InSyncSlackChannelRepr(
        id=item.id,
        name=item.name,
        created=item.created,
        is_archived=item.is_archived,
        is_channel=item.is_channel,
        is_ext_shared=item.is_ext_shared,
        is_general=item.is_general,
        is_group=item.is_group,
        is_im=item.is_im,
        is_member=item.is_member,
        is_mpim=item.is_mpim,
        is_org_shared=item.is_org_shared,
        is_pending_ext_shared=item.is_pending_ext_shared,
        is_private=item.is_private,
        is_shared=item.is_shared,
        topic=topic,
        updated=item.updated,
        updated_at=item.updated_at,
        created_at=item.created_at,
    )


def insync_slack_user_repr(item: InSyncSlackUser) -> dict:
    return InSyncSlackUserRepr(
        id=item.id,
        name=item.name,
        is_bot=item.is_bot,
        updated_at=item.updated_at,
        created_at=item.created_at,
    )


def linked_slack_channel_repr(item: LinkedSlackChannel) -> LinkedSlackChannelRepr:
    triage_channel = item.triage_channel
    triage_slack_channel = TriageSlackChannelRepr(
        channel_ref=triage_channel.slack_channel_ref,
        channel_name=triage_channel.slack_channel_name,
    )
    return LinkedSlackChannelRepr(
        channel_id=item.linked_slack_channel_id,
        channel_ref=item.slack_channel_ref,
        channel_name=item.slack_channel_name,
        triage_channel=triage_slack_channel,
    )


def issue_repr(item: Issue) -> IssueRepr:
    return IssueRepr(
        tenant_id=item.tenant_id,
        issue_id=item.issue_id,
        issue_number=item.issue_number,
        body=item.body,
        status=item.status,
        priority=item.priority,
        tags=item.tags,
        linked_slack_channel_id=item.linked_slack_channel_id,
    )
