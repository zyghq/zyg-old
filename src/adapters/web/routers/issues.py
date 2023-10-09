import logging
from typing import List

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.application.commands import CreateIssueCommand, SearchIssueCommand
from src.application.repr.api import issue_repr
from src.services.issue import CreateIssueService

logger = logging.getLogger(__name__)


class IssueCreateRequestBody(BaseModel):
    tenant_id: str
    slack_channel_id: str
    slack_message_ts: str
    body: str
    status: str | None
    priority: int | None
    tags: List[str] | None = None


class SearchIssueRequestBody(BaseModel):
    issue_id: str | None = None
    issue_number: int | None = None
    slack_channel_id: str | None = None
    slack_message_ts: str | None = None


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_issue(body: IssueCreateRequestBody):
    command = CreateIssueCommand(
        tenant_id=body.tenant_id,
        slack_channel_id=body.slack_channel_id,
        slack_message_ts=body.slack_message_ts,
        body=body.body,
        status=body.status,
        priority=body.priority,
        tags=body.tags,
    )
    service = CreateIssueService()
    issue = await service.create(command)
    return issue_repr(issue)


@router.post("/:search/")
async def search_issue(body: SearchIssueRequestBody):
    command = SearchIssueCommand(
        tenant_id="z320czxkpt5u",
        issue_id=body.issue_id,
        issue_number=body.issue_number,
        slack_channel_id=body.slack_channel_id,
        slack_message_ts=body.slack_message_ts,
    )
    service = CreateIssueService()
    result = await service.search(command)
    if result is None:
        return JSONResponse(status_code=200, content=[])
    issue = issue_repr(result)
    return JSONResponse(status_code=200, content=[issue.model_dump()])
