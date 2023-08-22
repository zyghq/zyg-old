from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from src.domain.commands import CreateSlackChannelCommand
from src.logger import logger
from src.services.inbox.channel import SlackChannelService

router = APIRouter()


class CreateSlackChannelRequestBody(BaseModel):
    """
    Represents the request body for creating an Slack channel.

    Currently we are keeping it simple and might add more attributes later, depending on the
    use cases.
    """

    channel_id: str | None = None
    name: str | None = None
    channel_type: str


@router.post("/create/")
async def create_channel(channel: CreateSlackChannelRequestBody):
    try:
        command = CreateSlackChannelCommand(
            channel_id=channel.channel_id,
            name=channel.name,
            channel_type=channel.channel_type,
        )
    except ValidationError as e:
        logger.error(e)
        logger.error("error creating command to create channel")
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
    result = await SlackChannelService().create(command)

    return result
