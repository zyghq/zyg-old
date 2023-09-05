from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from src.application.repr import for_sync_slack_conversation_item_repr
from src.services.tenant import TenantChannelSyncService

router = APIRouter()


class TenantSyncChannelsRequestBody(BaseModel):
    tenant_id: str
    types: List[str]


@router.post("/channels/sync/")
async def sync_channels(request_body: TenantSyncChannelsRequestBody):
    tenant_id = request_body.tenant_id
    print(f"invoking sync for tenant_id: {tenant_id}")
    types = request_body.types
    channel_sync_services = TenantChannelSyncService()
    results = channel_sync_services.sync_with_sync(types=types)
    response = (for_sync_slack_conversation_item_repr(item) for item in results)
    return response
