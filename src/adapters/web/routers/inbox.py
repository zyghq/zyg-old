from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, constr

from src.domain.commands.inbox import CreateInboxCommand
from src.logger import logger
from src.services.inbox import InboxService

router = APIRouter()


class CreateInboxRequestBody(BaseModel):
    """
    Represents the request body for creating an inbox.

    Currently we are keeping it simple and might add more attributes later, depending on the
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
    result = await InboxService().create(command)

    return result
