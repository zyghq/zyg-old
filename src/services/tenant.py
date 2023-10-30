import logging
from typing import Dict, List

from src.adapters.db.adapters import (
    InSyncChannelDBAdapter,
    InSyncSlackUserDBAdapter,
    TenantDBAdapter,
    UserDBAdapter,
)
from src.adapters.rpc.ext.slack import SlackWebAPIConnector
from src.application.commands import (
    SlackSyncUserCommand,
    TenantProvisionCommand,
    SyncChannelCommand,
)
from src.application.commands.slack import GetChannelsCommand, GetUsersCommand
from src.application.exceptions import SlackTeamReferenceException

# TODO: later this will be fetched from tenant context, and will be removed.
from src.config import SLACK_BOT_OAUTH_TOKEN
from src.domain.models import InSyncSlackUser, Tenant, User

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

    async def sync_now(self, command: SyncChannelCommand):
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
        results = slack_api.get_channels(
            GetChannelsCommand(types=",".join([t for t in types]))
        )
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
        self.user_db = UserDBAdapter()

    async def sync_now(
        self, command: SlackSyncUserCommand
    ) -> List[InSyncSlackUser] | List[Dict[str, InSyncSlackUser | User]]:
        """
        sync users in Slack workspace with synchronous approach
        """
        tenant = await self.tenant_db.get_by_id(command.tenant_id)
        logger.info(f"sync users for tenant with tenant context: `{tenant}`")

        tenant_context = tenant.build_context()
        slack_api = SlackWebAPIConnector(
            tenant_context=tenant_context,
            token=SLACK_BOT_OAUTH_TOKEN,  # TODO: disable this later when we can read token from tenant context # noqa
        )
        results = slack_api.get_users(GetUsersCommand(limit=1000))
        insync_users: List[InSyncSlackUser] = []
        for result in results:
            if result.is_bot or result.is_slackbot:
                continue
            insync_user = await self.insync_user_db.save(result)
            insync_users.append(insync_user)

        if command.upsert_user:
            insync_user_upserts = []
            for insync_user in insync_users:
                upserted_user = {}
                if insync_user.is_bot or insync_user.is_slackbot:
                    upserted_user["insync_user"] = insync_user
                    upserted_user["user"] = None
                    insync_user_upserts.append(upserted_user)
                    continue
                if insync_user.is_owner:
                    role = User.get_role_administrator()
                else:
                    role = User.default_role()
                user = User(
                    tenant_id=insync_user.tenant_id,
                    user_id=None,
                    slack_user_ref=insync_user.id_normalized,
                    name=insync_user.real_name,
                    role=role,
                )
                user = await self.user_db.save_by_tenant_id_slack_user_ref(user)
                upserted_user["insync_user"] = insync_user
                upserted_user["user"] = user
                insync_user_upserts.append(upserted_user)
            return insync_user_upserts
        else:
            return insync_users
