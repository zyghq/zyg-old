from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from src.adapters.tasker.tasks import add
from src.config import SLACK_APP_ID, SLACK_VERIFICATION_TOKEN
from src.logger import logger
from src.services import SlackEventService


class SlackCallbackEvent(BaseModel):
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


@router.get("/-/health/")
async def health_check() -> Any:
    result = add.delay(1, 200)
    print(result)
    return {"foobar": "foobar"}


@router.post("/-/slack/callback/")
async def slack_events(request: Request) -> Any:
    body = await request.json()

    token = body.get("token", None)
    if token is None:
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

    if token != SLACK_VERIFICATION_TOKEN:
        # todo: add async event admin notification
        return JSONResponse(
            status_code=403,
            content={
                "errors": [
                    {
                        "status": 403,
                        "title": "Forbidden",
                        "detail": "cannot authenticate the request came from Slack.",
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
            slack_event = SlackCallbackEvent(**body)
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

        slack_event_service = SlackEventService()
        error, result = await slack_event_service.capture_with_async_issue(
            slack_event.model_dump()
        )
        if error:
            logger.info("notify admin: error while capturing event.")
            logger.error(error)
            return JSONResponse(
                status_code=500,
                content={
                    "errors": [
                        {
                            "status": 500,
                            "title": "Internal Server Error",
                            "detail": "error while capturing event.",
                        }
                    ]
                },
            )
        logger.info(f"result after adding to database {result}")
        return JSONResponse(
            status_code=202,
            content={
                "detail": "captured",
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "detail": "ignored",
        },
    )
