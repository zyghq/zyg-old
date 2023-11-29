import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import engine
from src.db.repository import (
    MemberRepository,
    SlackBotRepository,
    SlackWorkspaceRepository,
    WorkspaceRepository,
    SlackChannelRepository,
)
from src.models.account import Account, Member, Workspace
from src.models.slack import SlackBot, SlackWorkspace, SlackChannelStatus
from src.tasks.slack import provision_pipeline
from src.web.deps import active_auth_account

logger = logging.getLogger(__name__)


router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
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


@router.post("/")
async def create_workspace(
    body: CreateWorkspaceRequest,
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
