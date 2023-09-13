import asyncio
from typing import Any, Dict

from src.domain.models import SlackEvent, Tenant
from src.services.task import lookup_event_handler
from src.worker import app


@app.task(bind=True, name="zygapp.slack_event_dispatch_handler")
def slack_event_dispatch_handler(self, context: Dict[str, Any], body: Dict[str, Any]):
    dispatch_id = context["dispatch_id"]
    dispatched_at = context["dispatched_at"]
    print(f"dispatch_id: {dispatch_id}")
    print(f"dispatched_at: {dispatched_at}")

    print("************************* context *************************")
    print(context)
    print("************************* body *************************")
    print(body)

    tenant = Tenant.from_dict(context["tenant"])
    print(f"running task for tenant: {tenant}")

    event = body["event"]
    subscribed_event = event["subscribed_event"]
    if SlackEvent.is_event_subscribed(subscribed_event):
        event_id = body["event_id"]
        payload = body["payload"]
        slack_event = SlackEvent.from_payload(
            tenant_id=tenant.tenant_id, payload=payload
        )
        slack_event.set_event_id(event_id)

        handler = lookup_event_handler(subscribed_event=subscribed_event)
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            handler(tenant=tenant, slack_event=slack_event)
        )
        print(f"result: {result}")
    else:
        pass
    return True


dd = {
    "tenant_id": "z320czxkpt5u",
    "event_id": "598cag9ghxyv",
    "slack_event_ref": "ev05mlbbdpfc",
    "event_ts": 1691953744,
    "payload": {
        "type": "event_callback",
        "event": {
            "ts": "1691953744.751639",
            "team": "T03NX4VMCRH",
            "text": "Hey",
            "type": "message",
            "user": "U03NGJTT5JT",
            "blocks": [
                {
                    "type": "rich_text",
                    "block_id": "=7/Nx",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"text": "Hey", "type": "text"}],
                        }
                    ],
                }
            ],
            "channel": "C05L3H90PL2",
            "event_ts": "1691953744.751639",
            "channel_type": "channel",
            "client_msg_id": "169fba12-e7db-4c7e-831b-19d603706aba",
        },
        "token": "LxFQN9LYmBb7Bt5dfMivVPNw",
        "team_id": "T03NX4VMCRH",
        "event_id": "Ev05MLBBDPFC",
        "api_app_id": "A05L1Q4VB63",
        "event_time": 1691953744,
        "authed_users": None,
        "event_context": "4-eyJldCI6Im1lc3NhZ2UiLCJ0aWQiOiJUMDNOWDRWTUNSSCIsImFpZCI6IkEwNUwxUTRWQjYzIiwiY2lkIjoiQzA1TDNIOTBQTDIifQ",
        "authorizations": [
            {
                "is_bot": False,
                "team_id": "T03NX4VMCRH",
                "user_id": "U03NGJTT5JT",
                "enterprise_id": None,
                "is_enterprise_install": False,
            }
        ],
        "context_team_id": "T03NX4VMCRH",
        "context_enterprise_id": None,
        "is_ext_shared_channel": False,
    },
    "is_ack": False,
    "event": {
        "tenant_id": "z320czxkpt5u",
        "event_id": None,
        "event_ts": 1691953744,
        "event": {
            "ts": "1691953744.751639",
            "team": "T03NX4VMCRH",
            "text": "Hey",
            "type": "message",
            "user": "U03NGJTT5JT",
            "blocks": [
                {
                    "type": "rich_text",
                    "block_id": "=7/Nx",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"text": "Hey", "type": "text"}],
                        }
                    ],
                }
            ],
            "channel": "C05L3H90PL2",
            "event_ts": "1691953744.751639",
            "channel_type": "channel",
            "client_msg_id": "169fba12-e7db-4c7e-831b-19d603706aba",
        },
        "inner_event_type": "message",
        "slack_event_ref": "ev05mlbbdpfc",
        "slack_channel_ref": "C05L3H90PL2",
        "subscribed_event": "message.channels",
    },
}
