import logging

from src.adapters.db.adapters import IssueDBAdapter, TenantDBAdapter
from src.application.commands import CreateIssueCommand
from src.domain.models import Issue

logger = logging.getLogger(__name__)


class CreateIssueService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.issue_db = IssueDBAdapter()

    async def create(self, command: CreateIssueCommand) -> Issue:
        tenant = await self.tenant_db.get_by_id(command.tenant_id)
        issue = Issue(
            tenant_id=tenant.tenant_id,
            issue_id=None,
            issue_number=None,
            body=command.body,
            status=command.status,
            priority=command.priority,
        )
        issue.tags = [t for t in command.tags]
        issue = await self.issue_db.save(issue=issue)
        return issue
