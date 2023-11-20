import asyncio
import logging
from typing import Any, Dict

from src.config import worker
from src.domain.models import SlackEvent, Tenant
from src.tasks.event import event_handler

logger = logging.getLogger(__name__)


@worker.task(bind=True, name="zyg.slack_event_handler")
def slack_event_handler(self, context: Dict[str, Any], body: Dict[str, Any]):
    dispatch_id = context["dispatch_id"]
    dispatched_at = context["dispatched_at"]
    print(f"dispatch_id: {dispatch_id}")
    print(f"dispatched_at: {dispatched_at}")

    tenant = Tenant.from_dict(context["tenant"])

    event = body["event"]
    subscribed_event = event["subscribed_event"]
    if SlackEvent.is_event_subscribed(subscribed_event):
        event_id = body["event_id"]
        payload = body["payload"]
        slack_event = SlackEvent.from_payload(
            tenant_id=tenant.tenant_id, event_id=event_id, payload=payload
        )

        handler = event_handler(subscribed_event)
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            handler(tenant=tenant, slack_event=slack_event)
        )

        print(f"result: {result}")
    else:
        logger.warning(f"unsupported event: {subscribed_event}")
        return False
    return True


@worker.task(bind=True, name="zyg.sync_slack_channels")
def sync_slack_channels(self, context: Dict[str, Any], body: Dict[str, Any]):
    logger.info("write code for syncing Slack channels for Tenant...")
