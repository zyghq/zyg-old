from typing import Callable, Dict, List

from src.adapters.db.adapters import IssueDBAdapter, TenantDBAdapter
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands.slack import UpdateMessageCommand
from src.application.repr.slack import (
    issue_closed_reply_blocks_repr,
    issue_closed_reply_text_repr,
)
from src.domain.models import Interaction, Tenant


class SlackInteractionService:
    supported_action_ids = ("action_close_issue",)

    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.issue_db = IssueDBAdapter()

    async def close_issue(self, tenant: Tenant, interaction: Interaction) -> None:
        metadata = interaction.message_metadata
        if not metadata:
            raise RuntimeError("no metadata found in interaction")

        # TODO: add interaction metadata parsing in domain model
        event_payload: dict = metadata.get("event_payload")
        issue_id = event_payload.get("issue_id")
        issue_number = event_payload.get("issue_number")

        print("TODO: close issue for issue_id: ", issue_id)

        slack_api = SlackWebAPIConnector(
            tenant_context=tenant.build_context(),
        )

        slack_user_ref = interaction.slack_user_ref_denormalized
        command = UpdateMessageCommand(
            channel=interaction.slack_channel_ref,
            ts=interaction.slack_message_ts,
            text=issue_closed_reply_text_repr(slack_user_ref),
            blocks=issue_closed_reply_blocks_repr(
                slack_user_ref=slack_user_ref, issue_number=issue_number
            ),
        )

        updated_metadata = {**metadata, "event_type": "issue_closed"}
        slack_api.update_message(command, metadata=updated_metadata)

        return True

    def _action_handlers(self, action_id: str) -> Callable:
        action_handlers = {
            "action_close_issue": self.close_issue,
        }
        handler = action_handlers.get(action_id, None)
        if not handler:
            raise ValueError(f"no handler for action_id: {action_id}")
        return handler

    async def handler(self, event: dict) -> None:
        actions: List[Dict] | None = event.get("actions", None)
        if not actions:
            return None

        interaction = Interaction(
            team=event.get("team"),
            channel=event.get("channel"),
            user=event.get("user"),
            message=event.get("message"),
            actions=event.get("actions"),
        )
        tenant = await self.tenant_db.get_by_slack_team_ref(interaction.slack_team_ref)

        results = []
        for action in actions:
            if action.get("action_id") not in self.supported_action_ids:
                continue
            func = self._action_handlers(action.get("action_id"))
            result = await func(tenant, interaction)
            result = {
                "action": action.get("action_id"),
                "result": result,
            }
            results.append(result)

        return results
