from src.adapters.db.adapters import TenantDBAdapter
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import TenantProvisionCommand
from src.application.exceptions import SlackTeamRefMapException
from src.domain.models import Tenant
from src.logger import logger


class TenantProvisionService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()

    async def provision(self, command: TenantProvisionCommand) -> Tenant:
        logger.info(
            f"`provision` tenant provision service invoked with command: `{command}`"
        )

        if command.slack_team_ref is not None:
            tenant = await self.tenant_db.find_by_slack_team_ref(command.slack_team_ref)
            if tenant:
                raise SlackTeamRefMapException(
                    f"slack team ref `{command.slack_team_ref}` "
                    + "is already mapped to a tenant"
                )

        tenant = Tenant(
            tenant_id=None,
            name=command.name,
        )
        tenant.set_slack_team_ref(command.slack_team_ref)
        tenant = await self.tenant_db.save(tenant)
        return tenant


class TenantChannelSyncService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.slack_api = SlackWebAPIConnector()

    def sync_with_sync(self, types=None):
        if types is None:
            types = ["public_channel"]
        """
        sync channels with syncronous approach
        """
        results = self.slack_api.get_conversation_list(",".join([t for t in types]))
        return results

    def sync_with_async(self):
        """
        sync channels with asyncronous approach
        """
        pass
