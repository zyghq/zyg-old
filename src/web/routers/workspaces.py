import logging

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db.repository import WorkspaceRepository
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
async def get_workspaces(account=Depends(active_auth_account)):
    repo = WorkspaceRepository()
    workspaces = await repo.find_all_by_account(account)
    workspaces = [workspace.to_dict() for workspace in workspaces]
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(workspaces),
    )


@router.get("/{workspace_id}/")
async def get_workspace(workspace_id: str, account=Depends(active_auth_account)):
    repo = WorkspaceRepository()
    workspace = await repo.find_by_account_and_id(account, workspace_id)
    if not workspace:
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder({"detail": "This workspace does not exist."}),
        )
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(workspace.to_dict()),
    )
