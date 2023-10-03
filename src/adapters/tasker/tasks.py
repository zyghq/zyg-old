import asyncio
from typing import Any, Dict

from src.adapters.tasker.init import app
from src.domain.models import SlackEvent, Tenant
from src.tasks.event import lookup_event_handler


@app.task(bind=True, name="zyg.slack_event_handler")
def slack_event_handler(self, context: Dict[str, Any], body: Dict[str, Any]):
    dispatch_id = context["dispatch_id"]
    dispatched_at = context["dispatched_at"]
    print(f"dispatch_id: {dispatch_id}")
    print(f"dispatched_at: {dispatched_at}")

    # print("************************* context *************************")
    # print(context)
    # print("************************* body *************************")
    # print(body)

    tenant = Tenant.from_dict(context["tenant"])
    print(f"running task for tenant: {tenant}")

    event = body["event"]
    subscribed_event = event["subscribed_event"]
    if SlackEvent.is_event_subscribed(subscribed_event):
        event_id = body["event_id"]
        payload = body["payload"]
        slack_event = SlackEvent.from_payload(
            tenant_id=tenant.tenant_id, event_id=event_id, payload=payload
        )
        handler = lookup_event_handler(subscribed_event)
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            handler(tenant=tenant, slack_event=slack_event)
        )
        print(f"result: {result}")
    else:
        pass
    return True
