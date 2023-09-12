import httpx

from src.application.commands import SearchLinkedSlackChannelCommand
from src.domain.models import Tenant


class APIConnector:
    def __init__(self, tenant: Tenant, base_url: str):
        self.tenant = tenant
        self.base_url = base_url

    async def search_linked_channel(self, command: SearchLinkedSlackChannelCommand):
        print("got command....", command)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tenants/channels/linked/:search/"
            )
            if response.status_code == 200:
                print(response.json())
            else:
                return None
