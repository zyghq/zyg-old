from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr

from src.application.commands import (
    LinkSlackChannelCommand,
    SearchSlackChannelCommand,
    SearchUserCommand,
    SlackSyncUserCommand,
    TenantSyncChannelCommand,
)
from src.application.repr.api import (
    insync_slack_channel_repr,
    insync_slack_user_repr,
    insync_slack_user_with_upsert,
    slack_channel_repr,
    user_repr,
)
from src.services.channel import SlackChannelService
from src.services.tenant import SlackChannelSyncService, SlackUserSyncService
from src.services.user import UserService

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
    slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None
    slack_channel_ref: Optional[str] = None


class SearchUserRequestBody(BaseModel):
    user_id: Optional[str] = None
    slack_user_ref: Optional[str] = None


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

    service = SlackChannelService()
    result = await service.link(command=command)
    slack_channel = slack_channel_repr(result)
    return slack_channel


@router.post("/channels/linked/:search/")
async def search_linked_channel(body: SearchLinkedChannelRequestBody):
    command = SearchSlackChannelCommand(
        tenant_id="z320czxkpt5u",
        slack_channel_id=body.slack_channel_id,
        slack_channel_name=body.slack_channel_name,
        slack_channel_ref=body.slack_channel_ref,
    )
    service = SlackChannelService()
    result = await service.search(command=command)
    if result is None:
        return JSONResponse(status_code=200, content=[])
    slack_channel = slack_channel_repr(result)
    return JSONResponse(status_code=200, content=[slack_channel.model_dump()])


@router.post("/users/:search/")
async def search_user(body: SearchUserRequestBody):
    command = SearchUserCommand(
        tenant_id="z320czxkpt5u",
        user_id=body.user_id,
        slack_user_ref=body.slack_user_ref,
    )
    result = await UserService().search(command=command)
    if result is None:
        return JSONResponse(status_code=200, content=[])
    user = user_repr(result)
    return JSONResponse(status_code=200, content=[user.model_dump()])
