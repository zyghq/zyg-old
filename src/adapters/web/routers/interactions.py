import json
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/-/slack/callback/")
async def slack_interaction(request: Request) -> Any:
    logger.info("received interaction from Slack API")
    form_data = await request.form()
    payload = form_data.get("payload")
    try:
        payload = json.loads(payload)
        print(payload)
    except json.JSONDecodeError as e:
        logger.error(f"error decoding payload: {e}")
        return JSONResponse(status_code=400, content={})
    return JSONResponse(status_code=200, content={})
