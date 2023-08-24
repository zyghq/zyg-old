from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from src.config import SLACK_APP_ID, SLACK_VERIFICATION_TOKEN
from src.domain.commands import SlackEventCommand
from src.logger import logger
from src.services.event.dispatcher import SlackEventServiceDispatcher


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
    authed_users: list[str] | None = None
    is_ext_shared_channel: bool | None = None
    context_team_id: str | None = None
    context_enterprise_id: str | None = None


router = APIRouter()


def is_slack_callback_valid(token: str, api_app_id: str):
    return token == SLACK_VERIFICATION_TOKEN and api_app_id == SLACK_APP_ID


@router.post("/-/slack/callback/")
async def slack_event(request: Request) -> Any:
    # we are not using Pydantic and FastAPI's request body validation
    # because this gives us more flexibility to handle the request body
    # as these events are received from Slack API and we dont have control over the request data model.
    body = await request.json()

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
                            "detail": "cannot authenticate the callback came from Slack.",
                        }
                    ]
                },
            )
        try:
            slack_request_body = SlackEventCallBackRequestBody(**body)
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

        event_type = slack_request_body.event.get("type", None)
        command = SlackEventCommand(
            event_id=slack_request_body.event_id,
            team_id=slack_request_body.team_id,
            api_app_id=slack_request_body.api_app_id,
            event=slack_request_body.event,
            event_type=event_type,
            event_ts=slack_request_body.event_time,
            callback_type=callback_type,
            context_team_id=slack_request_body.context_team_id,
            context_enterprise_id=slack_request_body.context_enterprise_id,
            metadata={
                "token": slack_request_body.token,
                "authorizations": slack_request_body.authorizations,
                "authed_users": slack_request_body.authed_users,
                "is_ext_shared_channel": slack_request_body.is_ext_shared_channel,
                "event_context": slack_request_body.event_context,
            },
        )
        try:
            #
            # pass the event command to the dispatcher
            # based on the inner `type` of the event we dispatch it to the
            # appropriate service.
            slack_event_service_dispatcher = SlackEventServiceDispatcher(
                command, capture=True, override=True
            )
            await slack_event_service_dispatcher.dispatch()
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

        return JSONResponse(
            status_code=202,
            content={
                "detail": "captured",
            },
        )

    # callback type that is not supported by us, assuming we receive from
    # Slack API, we ignore it by sending back 200 OK.
    # read more about Slack events API: https://api.slack.com/events
    return JSONResponse(
        status_code=200,
        content={
            "detail": "ignored",
        },
    )
