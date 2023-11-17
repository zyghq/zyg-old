import logging

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import engine
from src.db.repository import MemberRepository, WorkspaceRepository
from src.models.account import Member, Workspace
from src.web.deps import active_auth_account

logger = logging.getLogger(__name__)


router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.post("/")
async def create_workspace(
    body: CreateWorkspaceRequest, account=Depends(active_auth_account)
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
async def get_workspaces(account=Depends(active_auth_account)):
    async with engine.begin() as connection:
        repo = WorkspaceRepository(connection=connection)
        workspaces = await repo.find_all_by_account(account)
        workspaces = [workspace.to_dict() for workspace in workspaces]
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(workspaces),
        )


@router.get("/{slug}/")
async def get_workspace(slug: str, account=Depends(active_auth_account)):
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
