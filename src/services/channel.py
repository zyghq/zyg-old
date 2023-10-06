from src.adapters.db.adapters import (
    InSyncChannelDBAdapter,
    LinkedSlackChannelDBAdapter,
    TenantDBAdapter,
)
from src.application.commands import (
    LinkSlackChannelCommand,
    SearchLinkedSlackChannelCommand,
)
from src.domain.models import LinkedSlackChannel, TriageSlackChannel


class SlackChannelService:
    def __init__(self) -> None:
        self.tenant_db = TenantDBAdapter()
        self.insync_channel_db = InSyncChannelDBAdapter()
        self.linked_slack_channel_db = LinkedSlackChannelDBAdapter()

    async def link(self, command: LinkSlackChannelCommand) -> LinkedSlackChannel:
        tenant = await self.tenant_db.get_by_id(command.tenant_id)

        insync_slack_channel = (
            await self.insync_channel_db.get_by_tenant_id_slack_channel_ref(
                tenant_id=command.tenant_id, slack_channel_ref=command.slack_channel_ref
            )
        )
        linked_slack_channel = LinkedSlackChannel(
            tenant_id=tenant.tenant_id,
            linked_slack_channel_id=None,
            slack_channel_ref=insync_slack_channel.id,
            slack_channel_name=insync_slack_channel.name,
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

        linked_slack_channel.add_triage_channel(triage_slack_channel)
        linked_slack_channel = await self.linked_slack_channel_db.save(
            linked_slack_channel
        )
        return linked_slack_channel

    async def search(
        self, command: SearchLinkedSlackChannelCommand
    ) -> LinkedSlackChannel | None:
        """

        Searches based on the priority of the search fields
        """
        channel = None
        tenant_id = command.tenant_id
        if command.linked_slack_channel_id:
            channel = await self.linked_slack_channel_db.find_by_id(
                command.linked_slack_channel_id
            )
            return channel
        elif command.slack_channel_ref:
            channel = await self.linked_slack_channel_db.find_by_slack_channel_ref(
                command.slack_channel_ref
            )
            return channel
        else:
            channel = (
                await self.linked_slack_channel_db.find_by_tenant_id_slack_channel_name(
                    tenant_id=tenant_id, slack_channel_name=command.slack_channel_name
                )
            )
            return channel
