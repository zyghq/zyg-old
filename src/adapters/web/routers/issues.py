from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, constr

from src.domain.commands import CreateIssueCommand
from src.services.inbox.base import IssueService
from src.services.inbox.exceptions import SlackChannelLinkException
from src.logger import logger

router = APIRouter()


class CreateIssueRequestBody(BaseModel):
    """
    Represents the request body for creating an issue.
    """

    title: str | None = None
    body: constr(min_length=3)
    requester_id: str
    slack_channel_id: str


class CreateIssueResponseBody(BaseModel):
    """
    Represents the response body for creating an issue.
    """

    issue_id: str
    inbox_id: str
    requester_id: str
    title: str
    body: str


@router.post("/")
async def create_issue(issue: CreateIssueRequestBody):
    try:
        command = CreateIssueCommand(
            title=issue.title,
            body=issue.body,
            requester_id=issue.requester_id,
            slack_channel_id=issue.slack_channel_id,
        )
    except ValidationError as e:
        logger.error(e)
        logger.error("error creating command to create issue")
        return JSONResponse(
            status_code=503,
            content={
                "errors": [
                    {
                        "status": 503,
                        "title": "Service Unavailable",
                        "detail": "unable to create issue.",
                    }
                ]
            },
        )
    logger.info(f"invoking command to create issue: {command}")
    issue_service = IssueService()
    try:
        issue = await issue_service.create(command)
    except SlackChannelLinkException as e:
        logger.error(e)
        logger.error("cannot create issue without a slack channel linked inbox.")
        return JSONResponse(
            status_code=422,
            content={
                "errors": [
                    {
                        "status": 422,
                        "title": "Unprocessable Content",
                        "detail": "slack channel id is not linked to any inbox.",
                    }
                ]
            },
        )
    response = CreateIssueResponseBody(
        issue_id=issue.issue_id,
        inbox_id=issue.inbox_id,
        requester_id=issue.requester_id,
        title=issue.title,
        body=issue.body,
    )
    return response
