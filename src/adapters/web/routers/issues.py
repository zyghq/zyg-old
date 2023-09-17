import logging
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from src.application.commands import CreateIssueCommand
from src.application.repr import issue_repr
from src.services.issue import CreateIssueService

logger = logging.getLogger(__name__)


class IssueCreateRequestBody(BaseModel):
    tenant_id: str  # TODO: after auth we can read this from userauth token
    body: str
    status: str | None
    priority: int | None
    tags: List[str] = []


router = APIRouter()


@router.post("/")
async def create_issue(request_body: IssueCreateRequestBody):
    command = CreateIssueCommand(
        tenant_id=request_body.tenant_id,
        body=request_body.body,
        status=request_body.status,
        priority=request_body.priority,
        tags=request_body.tags,
    )
    service = CreateIssueService()
    issue = await service.create(command=command)
    return issue_repr(issue)
