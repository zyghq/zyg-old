import logging
from typing import List

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.application.commands import CreateIssueCommand
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


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_issue(request_body: IssueCreateRequestBody):
    command = CreateIssueCommand(
        tenant_id=request_body.tenant_id,
        slack_channel_id=request_body.slack_channel_id,
        slack_message_ts=request_body.slack_message_ts,
        body=request_body.body,
        status=request_body.status,
        priority=request_body.priority,
        tags=request_body.tags,
    )
    service = CreateIssueService()
    issue = await service.create(command)
    return issue_repr(issue)
