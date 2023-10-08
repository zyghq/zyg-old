import logging

from src.adapters.db.adapters import (
    IssueDBAdapter,
    SlackChannelDBAdapter,
    TenantDBAdapter,
)
from src.application.commands import CreateIssueCommand
from src.domain.models import Issue

logger = logging.getLogger(__name__)


class CreateIssueService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.issue_db = IssueDBAdapter()
        self.slack_channel_db = SlackChannelDBAdapter()

    async def create(self, command: CreateIssueCommand) -> Issue:
        tenant = await self.tenant_db.get_by_id(command.tenant_id)
        slack_channel_id = None

        if command.slack_channel_id:
            slack_channel = await self.slack_channel_db.get_by_id(
                command.slack_channel_id
            )
            slack_channel_id = slack_channel.slack_channel_id
        issue = Issue(
            tenant_id=tenant.tenant_id,
            issue_id=None,
            issue_number=None,
            body=command.body,
            status=command.status,
            priority=command.priority,
        )

        issue.tags = [t for t in command.tags]
        issue.slack_channel_id = slack_channel_id
        issue = await self.issue_db.save(issue)
        return issue
