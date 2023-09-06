from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from src.application.commands import TenantSyncChannelCommand
from src.application.repr import insync_slack_channel_item_repr
from src.services.tenant import TenantChannelSyncService

router = APIRouter()


class TenantSyncChannelsRequestBody(BaseModel):
    tenant_id: str
    types: List[str]


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
