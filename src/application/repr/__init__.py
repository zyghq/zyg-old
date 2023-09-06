from datetime import datetime

from pydantic import BaseModel

from src.domain.models import InSyncSlackChannelItem, SlackEvent


class TenantRepr(BaseModel):
    name: str
    tenant_id: str
    slack_team_ref: str


class SlackCallBackEventRepr(BaseModel):
    id: str


class InSyncSlackChannelItemRepr(BaseModel):
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


def slack_callback_event_repr(
    slack_event: SlackEvent,
) -> SlackCallBackEventRepr:
    pass


def insync_slack_channel_item_repr(
    item: InSyncSlackChannelItem,
) -> InSyncSlackChannelItemRepr:
    topic = {
        "value": item.topic.get("value", ""),
    }
    return InSyncSlackChannelItemRepr(
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
