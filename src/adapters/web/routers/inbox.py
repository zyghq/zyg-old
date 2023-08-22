from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, constr

from src.domain.commands import CreateInboxCommand
from src.logger import logger
from src.services.inbox.base import InboxService
from src.services.inbox.exceptions import (
    SlackChannelLinkException,
    SlackChannelNotFoundException,
)

router = APIRouter()


class CreateInboxRequestBody(BaseModel):
    """
    Represents the request body for creating an inbox.

    Currently we are keeping it simple and might add more attributes later,
    depending on the
    use cases.
    """

    name: constr(min_length=3, max_length=100)
    description: str | None = None
    slack_channel_id: str | None = None


@router.post("/create/")
async def create_inbox(inbox: CreateInboxRequestBody):
    try:
        command = CreateInboxCommand(
            name=inbox.name,
            description=inbox.description,
            slack_channel_id=inbox.slack_channel_id,
        )
    except ValidationError as e:
        logger.error(e)
        logger.error("error creating command to create inbox")
        return JSONResponse(
            status_code=503,
            content={
                "errors": [
                    {
                        "status": 503,
                        "title": "Service Unavailable",
                        "detail": "unable to create inbox.",
                    }
                ]
            },
        )

    logger.info(f"invoking command to create inbox: {command}")

    try:
        result = await InboxService().create(command)
    except SlackChannelNotFoundException:
        return JSONResponse(
            status_code=404,
            content={
                "errors": [
                    {
                        "status": 404,
                        "title": "Not Found",
                        "detail": "slack channel with "
                        + f"slack_channel_id: {command.slack_channel_id} not found",
                    }
                ]
            },
        )
    except SlackChannelLinkException:
        return JSONResponse(
            status_code=400,
            content={
                "errors": [
                    {
                        "status": 400,
                        "title": "Bad Request",
                        "detail": "slack channel with "
                        + f"slack_channel_id: {command.slack_channel_id} "
                        + "is already linked to an inbox",
                    }
                ]
            },
        )

    return result
