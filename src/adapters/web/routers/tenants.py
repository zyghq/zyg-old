from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, constr

from src.application.commands import LinkSlackChannelCommand, TenantSyncChannelCommand
from src.application.repr import (
    insync_slack_channel_item_repr,
    linked_slack_channel_repr,
)
from src.services.channel import ChannelLinkService
from src.services.tenant import TenantChannelSyncService

router = APIRouter()


class TenantSyncChannelsRequestBody(BaseModel):
    tenant_id: str
    types: List[str]


class LinkChannelRequestBody(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
    triage_slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)


@router.post("/channels/sync/")
async def sync_channels(request_body: TenantSyncChannelsRequestBody):
    command = TenantSyncChannelCommand(
        tenant_id=request_body.tenant_id,
        types=request_body.types,
    )
    channel_sync_services = TenantChannelSyncService()
    results = await channel_sync_services.sync_now(command=command)
    response = (insync_slack_channel_item_repr(r) for r in results)
    return response


@router.post("/channels/link/")
async def link_channel(request_body: LinkChannelRequestBody):
    command = LinkSlackChannelCommand(
        tenant_id=request_body.tenant_id,
        slack_channel_ref=request_body.slack_channel_ref,
        triage_slack_channel_ref=request_body.triage_slack_channel_ref,
    )

    channel_link_service = ChannelLinkService()
    result = await channel_link_service.link(command=command)
    linked_slack_channel = linked_slack_channel_repr(result)
    return linked_slack_channel
