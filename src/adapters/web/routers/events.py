import json
import logging
import os
from typing import Any, List

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from src.application.commands import SlackEventCallBackCommand
from src.application.repr.api import slack_callback_event_repr
from src.services.event import SlackEventCallBackService

SLACK_APP_ID = os.getenv("SLACK_APP_ID", "")
SLACK_VERIFICATION_TOKEN = os.getenv("SLACK_VERIFICATION_TOKEN", "")

logger = logging.getLogger(__name__)


class SlackEventCallBackRequestBody(BaseModel):
    """
    based on Slack API response for event callback:
    https://api.slack.com/events-api#receiving_events

    We assume these are the attributes that we receive from Slack API
    and we validate them using pydantic BaseModel.
    """

    event_id: str
    token: str
    team_id: str
    api_app_id: str
    event: dict | None = None
    type: str
    event_context: str
    event_time: int
    authorizations: dict | list[dict] | None = None
    authed_users: List[str] | None = None
    is_ext_shared_channel: bool | None = None
    context_team_id: str | None = None
    context_enterprise_id: str | None = None


router = APIRouter()


def is_slack_callback_valid(token: str, api_app_id: str):
    return token == SLACK_VERIFICATION_TOKEN and api_app_id == SLACK_APP_ID


@router.post("/-/slack/callback/")
async def slack_event(request: Request) -> Any:
    logger.info("received event from Slack API")
    # we are not using Pydantic and FastAPI's request body validation
    # because this gives us more flexibility to handle the request body
    # as these events are received from Slack API and we dont have
    # control over the request data model.
    body: dict = await request.json()

    print("**************** body ****************")
    print(json.dumps(body, indent=2))
    print("**************** body ****************")

    token = body.get("token", None)
    if token is None or token != SLACK_VERIFICATION_TOKEN:
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

    callback_type = body.get("type", None)
    if callback_type is None:
        logger.info("notify admin: callback type not received from Slack API response!")
        return JSONResponse(
            status_code=400,
            content={
                "errors": [
                    {
                        "status": 400,
                        "title": "Bad Request",
                        "detail": "callback type is missing or unsupported.",
                    }
                ]
            },
        )

    # based on callback type sent by Slack when doing initial verification
    # https://api.slack.com/events/url_verification
    # we send back the challenge value as it is
    if callback_type == "url_verification":
        challenge = body.get("challenge", None)
        return JSONResponse(
            status_code=200,
            content={
                "challenge": challenge,
            },
        )

    # based on callback type sent by Slack, this event is processed further.
    # https://api.slack.com/events-api#receiving_events
    # these events are processed for business logic.
    if callback_type == "event_callback":
        api_app_id = body.get("api_app_id", None)
        is_valid = is_slack_callback_valid(token, api_app_id)
        if not is_valid:
            logger.info("notify admin: event callback is not valid!")
            return JSONResponse(
                status_code=403,
                content={
                    "errors": [
                        {
                            "status": 403,
                            "title": "Forbidden",
                            "detail": "cannot authenticate the callback "
                            + "came from Slack.",
                        }
                    ]
                },
            )

        service = SlackEventCallBackService()
        try:
            if service.is_muted(body):
                logger.info("Slack event set to be muted will terminate here.")
                return JSONResponse(
                    status_code=200,
                    content={
                        "detail": "ignored",
                    },
                )
        except Exception as e:
            logger.error(
                "notify admin: error while checking if event is muted in metadata"
            )
            logger.error(e)
            return JSONResponse(
                status_code=503,
                content={
                    "errors": [
                        {
                            "status": 503,
                            "title": "Service Unavailable",
                            "detail": "error while checking if event is muted",
                        }
                    ]
                },
            )

        try:
            slack_event_cb = SlackEventCallBackRequestBody(**body)
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
            command = SlackEventCallBackCommand(
                slack_event_ref=slack_event_cb.event_id,
                slack_team_ref=slack_event_cb.team_id,
                event=slack_event_cb.event,
                event_dispatched_ts=slack_event_cb.event_time,
                payload=slack_event_cb.model_dump(),
            )
            slack_event = await service.dispatch(command)
        except Exception as e:
            logger.error("notify admin: error while capturing or dispatching event.")
            logger.error(e)
            return JSONResponse(
                status_code=503,
                content={
                    "errors": [
                        {
                            "status": 503,
                            "title": "Service Unavailable",
                            "detail": "error while capturing or processing event.",
                        }
                    ]
                },
            )

        event_repr = slack_callback_event_repr(slack_event)
        return JSONResponse(status_code=200, content=event_repr.model_dump())

    # callback type that is not supported by us, assuming we receive from
    # Slack API, we ignore it by sending back 200 OK.
    # read more about Slack events API: https://api.slack.com/events
    return JSONResponse(
        status_code=200,
        content={
            "detail": "ignored",
        },
    )
