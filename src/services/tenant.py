import logging

from src.adapters.db.adapters import (
    InSyncChannelDBAdapter,
    InSyncSlackUserDBAdapter,
    TenantDBAdapter,
)
from src.adapters.rpc.ext import SlackWebAPIConnector
from src.application.commands import (
    SlackSyncUserCommand,
    TenantProvisionCommand,
    TenantSyncChannelCommand,
)
from src.application.exceptions import SlackTeamReferenceException

# TODO: later this will be fetched from tenant context, and will be removed.
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import Tenant

logger = logging.getLogger(__name__)


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
                raise SlackTeamReferenceException(
                    f"slack team ref `{command.slack_team_ref}` "
                    + "is already mapped to a tenant"
                )

        tenant = Tenant(
            tenant_id=None,
            name=command.name,
            slack_team_ref=command.slack_team_ref,
        )
        tenant = await self.tenant_db.save(tenant)
        return tenant


class SlackChannelSyncService:
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

        tenant_context = tenant.build_context()
        slack_api = SlackWebAPIConnector(
            tenant_context=tenant_context,
            token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        )
        results = slack_api.get_conversation_list(",".join([t for t in types]))
        saved_results = []
        for result in results:
            saved_result = await self.insync_channel_db.save(result)
            saved_results.append(saved_result)
        return saved_results

    async def sync_task(self):
        """
        sync channels with asynchronous approach
        """
        raise NotImplementedError


class SlackUserSyncService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.insync_user_db = InSyncSlackUserDBAdapter()

    async def sync_now(self, command: SlackSyncUserCommand):
        """
        sync users in Slack workspace with syncronous approach
        """
        tenant = await self.tenant_db.get_by_id(command.tenant_id)
        logger.info(f"sync users for tenant with tenant context: `{tenant}`")

        tenant_context = tenant.build_context()
        slack_api = SlackWebAPIConnector(
            tenant_context=tenant_context,
            token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        )
        results = slack_api.get_users(limit=100)
        saved_results = []
        for result in results:
            saved_result = await self.insync_user_db.save(result)
            saved_results.append(saved_result)
        return saved_results
