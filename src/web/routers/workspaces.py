import logging
from typing import Annotated

import sqlalchemy as db
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import engine
from src.db.repository import (
    MemberRepository,
    SlackBotRepository,
    SlackChannelRepository,
    SlackWorkspaceRepository,
    WorkspaceRepository,
)
from src.db.schema import SlackWorkspaceDB, WorkspaceDB, SlackChannelDB
from src.models.account import Account, Member, Workspace
from src.models.slack import SlackBot, SlackChannelStatus, SlackWorkspace, SlackChannel
from src.tasks.slack import provision_pipeline
from src.web.deps import active_auth_account

logger = logging.getLogger(__name__)


router = APIRouter()


class CreateOrEditWorkspaceRequest(BaseModel):
    name: str


class SlackOAuthCallbackRequest(BaseModel):
    ok: bool
    access_token: str
    token_type: str
    scope: str
    bot_user_id: str
    app_id: str
    team: dict
    enterprise: dict | None = None
    authed_user: dict | None = None
    enterprise_id: str | None = None


class SlackChannelStatusRequest(BaseModel):
    status: SlackChannelStatus


# creates a workspace and a member for the account
@router.post("/")
async def create_workspace(
    body: CreateOrEditWorkspaceRequest,
    account: Annotated[Account, Depends(active_auth_account)],
):
    workspace = Workspace(
        account_id=account.account_id, workspace_id=None, name=body.name
    )
    async with engine.begin() as connection:
        workspace = await WorkspaceRepository(connection).save(workspace)
        member = Member(
            workspace_id=workspace.workspace_id,
            account_id=account.account_id,
            member_id=None,
            slug=None,
            role=Member.get_role_primary(),
        )
        member = await MemberRepository(connection).save(member)

    response = workspace.to_dict()
    response["member"] = {
        "member_id": member.member_id,
        "slug": member.slug,
        "role": member.role,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }
    return JSONResponse(
        status_code=201,
        content=jsonable_encoder(response),
    )


# get list of workspaces for the account
@router.get("/")
async def get_workspaces(account: Annotated[Account, Depends(active_auth_account)]):
    async with engine.begin() as connection:
        repo = WorkspaceRepository(connection)
        workspaces = await repo.find_all_by_account_id(account.account_id)
        workspaces = [workspace.to_dict() for workspace in workspaces]
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(workspaces),
    )


# get a workspace item for the account by slug
@router.get("/{slug}/")
async def get_workspace(
    slug: str, account: Annotated[Account, Depends(active_auth_account)]
):
    async with engine.begin() as connection:
        repo = WorkspaceRepository(connection)
        workspace = await repo.find_by_account_id_and_slug(account.account_id, slug)
        if not workspace:
            return JSONResponse(
                status_code=404,
                content=jsonable_encoder({"detail": "Workspace does not exist."}),
            )
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(workspace.to_dict()),
    )


# update a workspace for the account by slug
@router.patch("/{slug}/")
async def edit_workspace(
    slug: str,
    body: CreateOrEditWorkspaceRequest,
    account: Annotated[Account, Depends(active_auth_account)],
):
    async with engine.begin() as connection:
        workspace = await WorkspaceRepository(connection).find_by_account_id_and_slug(
            account.account_id, slug
        )
        if not workspace:
            return JSONResponse(
                status_code=404,
                content=jsonable_encoder({"detail": "Workspace does not exist."}),
            )

    workspace.name = body.name
    async with engine.begin() as connection:
        workspace = await WorkspaceRepository(connection).save(workspace)

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(workspace.to_dict()),
    )


# invoked by Slack OAuth flow - requires real world testing
# TODO: Needs testing in real Slack OAuth flow.
@router.post("/{slug}/slack/oauth/callback/")
async def slack_oauth_callback(
    body: SlackOAuthCallbackRequest,
    slug: str,
    account: Annotated[Account, Depends(active_auth_account)],
):
    access_token = body.access_token
    scope = body.scope
    bot_user_id = body.bot_user_id
    app_id = body.app_id

    team = body.team
    team_id = team["id"]
    team_name = team["name"]

    #
    # get the Workspace
    async with engine.begin() as connection:
        repo = WorkspaceRepository(connection)
        workspace = await repo.find_by_account_id_and_slug(account.account_id, slug)
        if not workspace:
            return JSONResponse(
                status_code=404,
                content=jsonable_encoder({"detail": "Workspace does not exist."}),
            )

    #
    # get the SlackWorkspace for the Workspace
    # if it doesn't exist, create it
    # make sure SlackBot exists for the new SlackWorkspace
    async with engine.begin() as connection:
        repo = SlackWorkspaceRepository(connection)
        slack_workspace = await repo.find_by_workspace_id(workspace.workspace_id)
        if not slack_workspace:
            slack_workspace = SlackWorkspace(
                workspace_id=workspace.workspace_id,
                ref=team_id,
                url="",
                name=team_name,
            )
            slack_workspace = await repo.save(slack_workspace)
            slack_bot = SlackBot(
                slack_workspace=slack_workspace,
                bot_user_ref=bot_user_id,
                app_ref=app_id,
                scope=scope,
                access_token=access_token,
            )
            slack_bot = await SlackBotRepository(connection).save(slack_bot)
        else:
            repo = SlackBotRepository(connection)
            slack_bot = await repo.find_by_slack_workspace(slack_workspace)
            if not slack_bot:
                slack_bot = SlackBot(
                    slack_workspace=slack_workspace,
                    bot_user_ref=bot_user_id,
                    app_ref=app_id,
                    scope=scope,
                    access_token=access_token,
                )
            slack_bot = await repo.upsert_by_slack_workspace(slack_bot)

    response = {
        "workspace": {
            "workspace_id": workspace.workspace_id,
            "slug": workspace.slug,
            "name": workspace.name,
        },
        "ref": slack_workspace.ref,
        "url": slack_workspace.url,
        "name": slack_workspace.name,
        "status": slack_workspace.status,
        "sync_status": slack_workspace.sync_status,
        "synced_at": slack_workspace.synced_at,
        "bot": {
            "bot_id": slack_bot.bot_id,
            "bot_user_ref": slack_bot.bot_user_ref,
            "app_ref": slack_bot.app_ref,
        },
    }
    # TODO: @sanchitrk - enable this after testing.
    # if slack_workspace.is_provisioning:
    context = {
        "account": account.to_dict(),
        "workspace": workspace.to_dict(),
    }
    provision_pipeline.delay(context)

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response),
    )


# get list of channels for the workspace
@router.get("/{slug}/slack/channels/")
async def get_workspace_channels(
    slug: str,
    account: Annotated[Account, Depends(active_auth_account)],
):
    async with engine.begin() as connection:
        query = (
            db.select(
                SlackWorkspaceDB.c.workspace_id,
                SlackWorkspaceDB.c.ref,
                SlackWorkspaceDB.c.url,
                SlackWorkspaceDB.c.name,
                SlackWorkspaceDB.c.status,
                SlackWorkspaceDB.c.sync_status,
                SlackWorkspaceDB.c.synced_at,
            )
            .join(WorkspaceDB)
            .where(
                db.and_(
                    WorkspaceDB.c.account_id == account.account_id,
                    WorkspaceDB.c.slug == slug,
                )
            )
        )
        rows = await connection.execute(query)
        result = rows.mappings().first()
        if not result:
            return JSONResponse(
                status_code=404,
                content=jsonable_encoder({"detail": "Workspace does not exist."}),
            )
        slack_workspace = SlackWorkspace(**result)
        print(slack_workspace)

    async with engine.begin() as connection:
        query = (
            db.select(
                SlackChannelDB.c.slack_workspace_ref,
                SlackChannelDB.c.channel_id,
                SlackChannelDB.c.channel_ref,
                SlackChannelDB.c.is_channel,
                SlackChannelDB.c.is_ext_shared,
                SlackChannelDB.c.is_general,
                SlackChannelDB.c.is_group,
                SlackChannelDB.c.is_im,
                SlackChannelDB.c.is_member,
                SlackChannelDB.c.is_mpim,
                SlackChannelDB.c.is_org_shared,
                SlackChannelDB.c.is_pending_ext_shared,
                SlackChannelDB.c.is_private,
                SlackChannelDB.c.is_shared,
                SlackChannelDB.c.name,
                SlackChannelDB.c.name_normalized,
                SlackChannelDB.c.created,
                SlackChannelDB.c.updated,
                SlackChannelDB.c.status,
                SlackChannelDB.c.synced_at,
                SlackChannelDB.c.created_at,
                SlackChannelDB.c.updated_at,
            )
            .where(SlackChannelDB.c.slack_workspace_ref == slack_workspace.ref)
            .order_by(SlackChannelDB.c.name)
            .limit(100)
        )

        rows = await connection.execute(query)
        results = rows.mappings().all()
        slack_channels = [SlackChannel(**result) for result in results]

    response = [
        {
            "channel_id": c.channel_id,
            "name": c.name,
            "is_listening": c.is_listening,
            "is_public": c.is_public,
            "synced_at": c.synced_at,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in slack_channels
    ]

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response),
    )


# update a Slack channel status by workspace slug and channel id
@router.patch("/{slug}/slack/channels/{channel_id}/status/")
async def update_slack_channel_status(
    body: SlackChannelStatusRequest,
    slug: str,
    channel_id: str,
    account: Annotated[Account, Depends(active_auth_account)],
):
    async with engine.begin() as connection:
        workspace = await WorkspaceRepository(connection).find_by_account_id_and_slug(
            account.account_id, slug
        )
        if not workspace:
            return JSONResponse(
                status_code=404,
                content=jsonable_encoder({"detail": "Workspace does not exist."}),
            )

    async with engine.begin() as connection:
        slack_channel = await SlackChannelRepository(
            connection
        ).update_status_by_channel_id(channel_id, body.status.value)

    response = {
        "channel_id": slack_channel.channel_id,
        "status": slack_channel.status,
        "channel_ref": slack_channel.channel_ref,
        "synced_at": slack_channel.synced_at,
        "created_at": slack_channel.created_at,
        "updated_at": slack_channel.updated_at,
    }
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response),
    )
