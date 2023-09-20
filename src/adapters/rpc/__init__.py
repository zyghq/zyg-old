import httpx

from src.application.commands import CreateIssueCommand
from src.config import ZYG_BASE_URL
from src.domain.models import TenantContext


class WebAPIConnector:
    def __init__(self, tenant_context: TenantContext, base_url=ZYG_BASE_URL) -> None:
        self.tenant_context = tenant_context
        self.base_url = base_url

    async def create_issue(self, command: CreateIssueCommand):
        response = httpx.post(
            f"{self.base_url}/issues/",
            headers={
                "content-type": "application/json",
            },
            json={
                "tenant_id": command.tenant_id,
                "body": command.body,
                "status": command.status,
                "priority": command.priority,
                "tags": command.tags,
            },
        )
        print("************* http response **************")
        print(response)
        print("**************** http response *************")

        if response.status_code == 200:
            response_json = response.json()
            return (None, response_json)
        return (None, None)
