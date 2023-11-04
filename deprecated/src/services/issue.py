import logging

from src.adapters.db.adapters import (
    IssueDBAdapter,
    SlackChannelDBAdapter,
    TenantDBAdapter,
)
from src.application.commands import CreateIssueCommand, SearchIssueCommand
from src.domain.models import Issue

logger = logging.getLogger(__name__)


class CreateIssueService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.issue_db = IssueDBAdapter()
        self.slack_channel_db = SlackChannelDBAdapter()

    async def create(self, command: CreateIssueCommand) -> Issue:
        tenant = await self.tenant_db.get_by_id(command.tenant_id)
        slack_channel = await self.slack_channel_db.get_by_id(command.slack_channel_id)

        issue = Issue(
            tenant_id=tenant.tenant_id,
            issue_id=None,
            issue_number=None,
            slack_channel_id=slack_channel.slack_channel_id,
            slack_message_ts=command.slack_message_ts,
            body=command.body,
            status=command.status,
            priority=command.priority,
        )

        issue.tags = command.tags
        issue = await self.issue_db.save(issue)
        return issue

    async def search(self, command: SearchIssueCommand) -> Issue | None:
        if command.issue_id:
            return await self.issue_db.find_by_id(command.issue_id)
        elif command.issue_number:
            return await self.issue_db.find_by_number(command.issue_number)
        elif command.slack_channel_id and command.slack_message_ts:
            return await self.issue_db.find_by_slack_channel_id_message_ts(
                command.slack_channel_id, command.slack_message_ts
            )
        else:
            return None
