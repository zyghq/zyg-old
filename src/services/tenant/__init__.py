from src.adapters.db.adapters import InSyncChannelDBAdapter, TenantDBAdapter
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import TenantProvisionCommand, TenantSyncChannelCommand
from src.application.exceptions import SlackTeamRefMapException

# TODO: later this will be fetched from tenant context, and will be removed.
from src.config import SLACK_BOT_OAUTH_TOKEN
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
        self.insync_channel_db = InSyncChannelDBAdapter()

    async def sync_now(self, command: TenantSyncChannelCommand):
        """
        sync channels with synchronous approach
        """
        types = command.types
        if types is None:
            types = ["public_channel"]

        tenant = await self.tenant_db.get_by_id(command.tenant_id)
        logger.info(f"sync channels for tenant with tenant context: `{tenant}`")

        slack_api = SlackWebAPIConnector.for_tenant(
            tenant=tenant,
            token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        )
        results = slack_api.get_conversation_list(",".join([t for t in types]))
        saved_results = []
        for result in results:
            saved_result = await self.insync_channel_db.save(result)
            saved_results.append(saved_result)
        return saved_results

    def sync_task(self):
        """
        sync channels with asynchronous approach
        """
        raise NotImplementedError
