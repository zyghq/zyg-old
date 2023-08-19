from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from src.config import SLACK_APP_ID, SLACK_VERIFICATION_TOKEN
from src.logger import logger
from src.services.events import SlackEventService
from src.services.exceptions import SlackCaptureException


class SlackCallbackRequestEvent(BaseModel):
    event_id: str
    token: str
    team_id: str
    api_app_id: str
    event: dict | None = None
    type: str
    event_context: str
    event_time: int
    authorizations: dict | list[dict] | None = None
    authed_users: list[str] | None = None
    is_ext_shared_channel: bool | None = None
    context_team_id: str | None = None
    context_enterprise_id: str | None = None


router = APIRouter()


def is_slack_callback_valid(token: str, api_app_id: str):
    return token == SLACK_VERIFICATION_TOKEN and api_app_id == SLACK_APP_ID


@router.post("/-/slack/callback/")
async def slack_events(request: Request) -> Any:
    body = await request.json()

    token = body.get("token", None)
    if token is None or token != SLACK_VERIFICATION_TOKEN:
        # todo: add async event admin notification
        return JSONResponse(
            status_code=401,
            content={
                "errors": [
                    {
                        "status": 401,
                        "title": "Unauthorized",
                        "detail": "cannot verify the request came from Slack.",
                    }
                ]
            },
        )

    event_type = body.get("type", None)
    if event_type is None:
        logger.info(
            "notify admin: event type not received from Slack API response!"
        )  # todo: add logger and admin notification.
        return JSONResponse(
            status_code=400,
            content={
                "errors": [
                    {
                        "status": 400,
                        "title": "Bad Request",
                        "detail": "event type is missing or unsupported.",
                    }
                ]
            },
        )

    if event_type == "url_verification":
        challenge = body.get("challenge", None)
        return JSONResponse(
            status_code=200,
            content={
                "challenge": challenge,
            },
        )

    if event_type == "event_callback":
        api_app_id = body.get("api_app_id", None)
        is_valid = is_slack_callback_valid(token, api_app_id)
        if not is_valid:
            logger.info(
                "notify admin: event callback is not valid!"
            )  # todo: add admin notification service
            return JSONResponse(
                status_code=403,
                content={
                    "errors": [
                        {
                            "status": 403,
                            "title": "Forbidden",
                            "detail": "cannot authenticate the callback came from Slack.",
                        }
                    ]
                },
            )
        try:
            slack_event_request = SlackCallbackRequestEvent(**body)
        except ValidationError as e:
            logger.info("notify admin: event callback is not valid!")
            logger.warning(e)
            return JSONResponse(
                status_code=400,
                content={
                    "errors": [
                        {
                            "status": 400,
                            "title": "Bad Request",
                            "detail": "event callback validation failed.",
                        }
                    ]
                },
            )
        try:
            slack_event_service = SlackEventService()
            slack_event = {
                "event_id": slack_event_request.event_id,
                "team_id": slack_event_request.team_id,
                "event": slack_event_request.event,
                "event_type": slack_event_request.type,
                "event_ts": slack_event_request.event_time,
                "metadata": {
                    "token": slack_event_request.token,
                    "authorizations": slack_event_request.authorizations,
                    "authed_users": slack_event_request.authed_users,
                    "is_ext_shared_channel": slack_event_request.is_ext_shared_channel,
                    "context_team_id": slack_event_request.context_team_id,
                    "context_enterprise_id": slack_event_request.context_enterprise_id,
                },
            }
            await slack_event_service.capture(slack_event)
            return JSONResponse(
                status_code=202,
                content={
                    "detail": "captured",
                },
            )
        except (SlackCaptureException, Exception) as e:
            logger.error("notify admin: error while capturing event.")
            logger.error(e)
            return JSONResponse(
                status_code=503,
                content={
                    "errors": [
                        {
                            "status": 503,
                            "title": "Internal Server Error",
                            "detail": "error while capturing event.",
                        }
                    ]
                },
            )

    return JSONResponse(
        status_code=200,
        content={
            "detail": "ignored",
        },
    )
