from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import SLACK_APP_ID, SLACK_VERIFICATION_TOKEN

router = APIRouter()


class SlackEventCallbackBody(BaseModel):
    token: str
    team_id: str
    api_app_id: str
    event: dict | None = None
    type: str
    authorizations: list | dict | None = None
    event_context: str
    event_id: str
    event_time: int


def is_slack_callback_valid(token: str, api_app_id: str):
    return token == SLACK_VERIFICATION_TOKEN and api_app_id == SLACK_APP_ID


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
        print(
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
            print(
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
        slack_callback_event = SlackEventCallbackBody(**body)
        print("******************")
        print(slack_callback_event)
        print("******************")
        # todo: create a service to handle the request
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
