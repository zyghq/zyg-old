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
)
from src.models.account import Account, Member, Workspace
from src.models.slack import SlackBot, SlackWorkspace
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


@router.post("/")
async def create_workspace(
    body: CreateWorkspaceRequest,
    account: Annotated[Account, Depends(active_auth_account)],
):
    workspace = Workspace(account=account, workspace_id=None, name=body.name)
    async with engine.begin() as connection:
        workspace = await WorkspaceRepository(connection=connection).save(workspace)
        member = Member(
            workspace=workspace,
            account=account,
            role=Member.get_role_primary(),
        )
        member = await MemberRepository(connection=connection).save(member)
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
        repo = WorkspaceRepository(connection=connection)
        workspaces = await repo.find_all_by_account(account)
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
        repo = WorkspaceRepository(connection=connection)
        workspace = await repo.find_by_account_and_slug(account, slug)
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
        repo = WorkspaceRepository(connection=connection)
        workspace = await repo.find_by_account_and_slug(account, slug)
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
        repo = SlackWorkspaceRepository(connection=connection)
        slack_workspace = await repo.find_by_workspace(workspace)
        if not slack_workspace:
            slack_workspace = SlackWorkspace(
                workspace=workspace,
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
            slack_bot = await SlackBotRepository(connection=connection).save(slack_bot)
        else:
            repo = SlackBotRepository(connection=connection)
            slack_bot = await repo.find_by_workspace(slack_workspace)
            if not slack_bot:
                slack_bot = SlackBot(
                    slack_workspace=slack_workspace,
                    bot_user_ref=bot_user_id,
                    app_ref=app_id,
                    scope=scope,
                    access_token=access_token,
                )
            slack_bot = await repo.upsert_by_workspace(slack_bot)

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
