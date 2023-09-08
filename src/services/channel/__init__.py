from src.adapters.db.adapters import (
    InSyncChannelDBAdapter,
    LinkedSlackChannelDBAdapter,
    TenantDBAdapter,
)
from src.application.commands import LinkSlackChannelCommand
from src.domain.models import LinkedSlackChannel, TriageSlackChannel


class ChannelLinkService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.insync_channel_db = InSyncChannelDBAdapter()
        self.linked_slack_channel_db = LinkedSlackChannelDBAdapter()

    async def link(self, command: LinkSlackChannelCommand):
        tenant = await self.tenant_db.get_by_id(command.tenant_id)

        insync_slack_channel = (
            await self.insync_channel_db.get_by_tenant_id_slack_channel_ref(
                tenant_id=command.tenant_id, slack_channel_ref=command.slack_channel_ref
            )
        )
        insync_slack_channel_for_triage = (
            await self.insync_channel_db.get_by_tenant_id_slack_channel_ref(
                tenant_id=command.tenant_id,
                slack_channel_ref=command.triage_slack_channel_ref,
            )
        )
        triage_slack_channel = TriageSlackChannel(
            tenant_id=tenant.tenant_id,
            slack_channel_ref=insync_slack_channel_for_triage.id,
            slack_channel_name=insync_slack_channel_for_triage.name,
        )

        linked_slack_channel = LinkedSlackChannel(
            tenant_id=tenant.tenant_id,
            linked_slack_channel_id=None,
            slack_channel_ref=insync_slack_channel.id,
            slack_channel_name=insync_slack_channel.name,
        )
        linked_slack_channel.add_triage_channel(triage_slack_channel)

        linked_slack_channel = await self.linked_slack_channel_db.save(
            linked_slack_channel
        )
        return linked_slack_channel
