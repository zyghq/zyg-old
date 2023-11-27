from datetime import datetime
from enum import Enum
from attrs import define, field
from .base import AbstractEntity, AbstractValueObject

# A note on SlackWorkspaceStatus:
#
# Currently we are not sure what the status of a SlackWorkspace should be.
# Have added basic states for now.
#
# PROVISIONING:
#   - Slack Workspace is being provisioned.
#   - This is the initial state after oauth if the workspace does not exist.
# READY:
#   - Slack Workspace is ready to be used.
#   - Now, this is the end working state, but we may want to add more states in between.
# DEACTIVATED:
#   - Slack Workspace has been deactivated or oauth is deleted.
#   - This needs to be handled in the future, what happens when a workspace is deactivated?


class SlackWorkspaceStatus(Enum):
    READY = "ready"
    PROVISIONING = "provisioning"
    DEACTIVATED = "deactivated"


class SlackSyncStatus(Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    ABORTED = "aborted"


class SlackWorkspace(AbstractEntity):
    def __init__(
        self,
        workspace_id: str,
        ref: str,
        url: str,
        name: str,
        status: SlackWorkspaceStatus | None | str = SlackWorkspaceStatus.PROVISIONING,
        sync_status: SlackSyncStatus | None | str = SlackSyncStatus.PENDING,
        synced_at: datetime | None = None,
    ) -> None:
        self.workspace_id = workspace_id
        self.ref = ref
        self.url = url
        self.name = name

        if status is None:
            status = SlackWorkspaceStatus.PROVISIONING
        if isinstance(status, str):
            status = SlackWorkspaceStatus(status)

        assert isinstance(status, SlackWorkspaceStatus)

        if sync_status is None:
            sync_status = SlackSyncStatus.PENDING
        if isinstance(sync_status, str):
            sync_status = SlackSyncStatus(sync_status)

        assert isinstance(sync_status, SlackSyncStatus)

        self._status = status

        self._sync_status = sync_status
        self.synced_at = synced_at

    @property
    def status(self) -> str:
        if self._status is None:
            return SlackWorkspaceStatus.PROVISIONING.value
        return self._status.value

    @status.setter
    def status(self, status: SlackWorkspaceStatus | str) -> None:
        if isinstance(status, str):
            status = SlackWorkspaceStatus(status)
        self._status = status

    @property
    def sync_status(self) -> str:
        if self._sync_status is None:
            return SlackSyncStatus.PENDING.value
        return self._sync_status.value

    @sync_status.setter
    def sync_status(self, sync_status: SlackSyncStatus | str) -> None:
        if isinstance(sync_status, str):
            sync_status = SlackSyncStatus(sync_status)
        self._sync_status = sync_status

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackWorkspace):
            return NotImplemented
        return self.workspace_id == other.workspace_id and self.ref == other.ref

    def __repr__(self) -> str:
        return f"""SlackWorkspace(
            workspace_id={self.workspace_id},
            ref={self.ref},
            url={self.url},
            name={self.name},
            status={self.status},
            sync_status={self.sync_status},
            synced_at={self.synced_at},
        )"""

    def equals_by_ref(self, other: object) -> bool:
        if not isinstance(other, SlackWorkspace):
            return NotImplemented
        return self.ref == other.ref

    @staticmethod
    def status_provisioning() -> str:
        return SlackWorkspaceStatus.PROVISIONING.value

    @staticmethod
    def status_ready() -> str:
        return SlackWorkspaceStatus.READY.value

    @staticmethod
    def status_deactivated() -> str:
        return SlackWorkspaceStatus.DEACTIVATED.value

    @property
    def is_provisioning(self) -> bool:
        return self._status == SlackWorkspaceStatus.PROVISIONING

    @property
    def is_ready(self) -> bool:
        return self._status == SlackWorkspaceStatus.READY

    @property
    def is_deactivated(self) -> bool:
        return self._status == SlackWorkspaceStatus.DEACTIVATED

    @staticmethod
    def sync_status_pending() -> str:
        return SlackSyncStatus.PENDING.value

    @staticmethod
    def sync_status_syncing() -> str:
        return SlackSyncStatus.SYNCING.value

    @staticmethod
    def sync_status_completed() -> str:
        return SlackSyncStatus.COMPLETED.value

    @staticmethod
    def get_sync_status_aborted() -> str:
        return SlackSyncStatus.ABORTED.value

    @classmethod
    def from_dict(cls, workspace_id: str, values: dict) -> "SlackWorkspace":
        return cls(
            workspace_id=workspace_id,
            ref=values.get("ref"),
            url=values.get("url"),
            name=values.get("name"),
            status=values.get("status"),
            sync_status=values.get("sync_status"),
            synced_at=cls._parse_datetime(values.get("synced_at", None)),
        )


class SlackBot(AbstractEntity):
    def __init__(
        self,
        slack_workspace: SlackWorkspace,
        bot_user_ref: str,
        app_ref: str,
        scope: str,
        access_token: str,
        bot_id: str | None = None,
        bot_ref: str | None = None,
    ):
        self.slack_workspace = slack_workspace
        self.bot_user_ref = bot_user_ref
        self.app_ref = app_ref
        self.scope = scope
        self.access_token = access_token

        self.bot_id = bot_id
        self.bot_ref = bot_ref

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackBot):
            return NotImplemented
        return (
            self.slack_workspace == other.slack_workspace
            and self.bot_id == other.bot_id
        )

    def equals_by_bot_user_ref(self, other: object) -> bool:
        if not isinstance(other, SlackBot):
            return NotImplemented
        return (
            self.slack_workspace == other.slack_workspace
            and self.bot_user_ref == other.bot_user_ref
        )

    def __repr__(self) -> str:
        return f"""SlackBot(
            slack_workspace={self.slack_workspace},
            bot_id={self.bot_id},
            bot_user_ref={self.bot_user_ref},
            bot_ref={self.bot_ref},
            app_ref={self.app_ref},
        )"""

    @classmethod
    def from_dict(cls, slack_workspace: SlackWorkspace, values: dict) -> "SlackBot":
        return cls(
            slack_workspace=slack_workspace,
            bot_id=values.get("bot_id"),
            bot_user_ref=values.get("bot_user_ref"),
            bot_ref=values.get("bot_ref"),
            app_ref=values.get("app_ref"),
            scope=values.get("scope"),
            access_token=values.get("access_token"),
        )


class SlackChannelStatus(Enum):
    MUTE = "mute"
    LISTEN = "listen"


@define(frozen=True, kw_only=True)
class SlackChannel(AbstractValueObject):
    slack_workspace: SlackWorkspace
    channel_id: str | None = field(default=None)
    channel_ref: str
    is_channel: bool
    is_ext_shared: bool
    is_general: bool
    is_group: bool
    is_im: bool
    is_member: bool
    is_mpim: bool
    is_org_shared: bool
    is_pending_ext_shared: bool
    is_private: bool
    is_shared: bool
    name: str
    name_normalized: str
    created: int
    updated: int
    status: str = field(default=SlackChannelStatus.MUTE.value)
    synced_at: datetime | None = field(default=None)
    created_at: datetime | None = field(default=None)
    updated_at: datetime | None = field(default=None)

    @staticmethod
    def status_mute() -> str:
        return SlackChannelStatus.MUTE.value

    @staticmethod
    def status_listen() -> str:
        return SlackChannelStatus.LISTEN.value

    @classmethod
    def from_dict(cls, slack_workspace: SlackWorkspace, values: dict) -> "SlackChannel":
        return cls(
            slack_workspace=slack_workspace,
            channel_id=values.get("channel_id", None),
            channel_ref=values.get("id"),
            is_channel=values.get("is_channel"),
            is_ext_shared=values.get("is_ext_shared"),
            is_general=values.get("is_general"),
            is_group=values.get("is_group"),
            is_im=values.get("is_im"),
            is_member=values.get("is_member"),
            is_mpim=values.get("is_mpim"),
            is_org_shared=values.get("is_org_shared"),
            is_pending_ext_shared=values.get("is_pending_ext_shared"),
            is_private=values.get("is_private"),
            is_shared=values.get("is_shared"),
            name=values.get("name"),
            name_normalized=values.get("name_normalized"),
            created=values.get("created"),
            updated=values.get("updated"),
            status=values.get("status", None),
            synced_at=values.get("synced_at", None),
            created_at=values.get("created_at", None),
            updated_at=values.get("updated_at", None),
        )
