from src.adapters.db.adapters import IssueDBAdapter, TenantDBAdapter
from src.domain.models import Issue, Tenant

from typing import List, Dict


class SlackInteractionService:
    supported_actions = ("action_close_issue",)

    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.issue_db = IssueDBAdapter()

    async def close_issue(self, event: dict) -> None:
        print("**************** close issue ****************")
        return

    async def handler(self, event: dict) -> None:
        actions: List[Dict] | None = event.get("actions", None)
        if not actions:
            return None

        for action in actions:
            action_id = action.get("action_id", None)
            if action_id in self.supported_actions:
                break
        action_id = action.get("action_id")

        if action_id == "action_close_issue":
            return await self.close_issue(event)
        return None




