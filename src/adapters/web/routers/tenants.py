from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr

from src.application.commands import (
    LinkSlackChannelCommand,
    SearchLinkedSlackChannelCommand,
    SlackSyncUserCommand,
    TenantSyncChannelCommand,
)
from src.application.repr.api import (
    insync_slack_channel_repr,
    insync_slack_user_repr,
    insync_slack_user_with_upsert,
    linked_slack_channel_repr,
)
from src.services.channel import LinkSlackChannelService
from src.services.tenant import SlackChannelSyncService, SlackUserSyncService

router = APIRouter()


class TenantSyncChannelsRequestBody(BaseModel):
    tenant_id: str
    types: List[str]


class TenantSyncUsersRequestBody(BaseModel):
    tenant_id: str
    upsert_user: bool = False


class LinkChannelRequestBody(BaseModel):
    tenant_id: str
    slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)
    triage_slack_channel_ref: constr(min_length=3, max_length=255, to_lower=True)


class SearchLinkedChannelRequestBody(BaseModel):
    linked_slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None
    slack_channel_ref: Optional[str] = None


@router.post("/channels/sync/")
async def sync_channels(body: TenantSyncChannelsRequestBody):
    command = TenantSyncChannelCommand(
        tenant_id=body.tenant_id,
        types=body.types,
    )
    sync_service = SlackChannelSyncService()
    results = await sync_service.sync_now(command=command)
    response = (insync_slack_channel_repr(r) for r in results)
    return response


@router.post("/users/sync/")
async def sync_users(body: TenantSyncUsersRequestBody):
    command = SlackSyncUserCommand(
        tenant_id=body.tenant_id,
        upsert_user=body.upsert_user,
    )
    sync_service = SlackUserSyncService()
    results = await sync_service.sync_now(command=command)
    if command.upsert_user:
        response = (insync_slack_user_with_upsert(r) for r in results)
        return response
    response = (insync_slack_user_repr(r) for r in results)
    return response


@router.post("/channels/link/")
async def link_channel(body: LinkChannelRequestBody):
    command = LinkSlackChannelCommand(
        tenant_id=body.tenant_id,
        slack_channel_ref=body.slack_channel_ref,
        triage_slack_channel_ref=body.triage_slack_channel_ref,
    )

    service = LinkSlackChannelService()
    result = await service.link(command=command)
    linked_slack_channel = linked_slack_channel_repr(result)
    return linked_slack_channel


@router.post("/channels/linked/:search/")
async def search_linked_channel(body: SearchLinkedChannelRequestBody):
    command = SearchLinkedSlackChannelCommand(
        tenant_id="z320czxkpt5u",
        linked_slack_channel_id=body.linked_slack_channel_id,
        slack_channel_name=body.slack_channel_name,
        slack_channel_ref=body.slack_channel_ref,
    )
    service = LinkSlackChannelService()
    result = await service.search(command=command)
    if result is None:
        return JSONResponse(status_code=200, content=[])
    linked_slack_channel = linked_slack_channel_repr(result)
    return JSONResponse(status_code=200, content=[linked_slack_channel.model_dump()])
