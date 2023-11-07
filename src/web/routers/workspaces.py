import logging

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db.repository import AccountRepository, WorkspaceRepository
from src.models.account import Workspace
from src.web.deps import active_auth_account

logger = logging.getLogger(__name__)


router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
    name: str
    logo_url: str | None = None


@router.post("/")
async def create_workspace(
    body: CreateWorkspaceRequest, account=Depends(active_auth_account)
):
    # auth_user_id = "123456789"
    # account = await AccountRepository().get_by_auth_user_id(auth_user_id)
    workspace = Workspace(
        workspace_id=None,
        name=body.name,
        created_at=None,
        updated_at=None,
    )
    workspace.add_account(account)
    workspace.add_logo_url(body.logo_url)
    workspace = await WorkspaceRepository().save(workspace)
    return JSONResponse(
        status_code=201,
        content=jsonable_encoder(workspace.to_dict()),
    )


@router.get("/")
async def get_workspaces(request: Request, account=Depends(active_auth_account)):
    # headers = request.headers
    # cookies = request.cookies
    # print(headers)
    # print(cookies)
    # auth_user_id = "123456789"
    # account = await AccountRepository().get_by_auth_user_id(account.auth_user_id)
    repo = WorkspaceRepository()
    workspaces = await repo.find_all_by_account(account)
    workspaces = [workspace.to_dict() for workspace in workspaces]
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(workspaces),
    )
