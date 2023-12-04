from datetime import datetime
from enum import Enum

from .base import AbstractEntity


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
    """
    Represents a Slack Workspace.

    Important fields:
    - status
    - sync_status

    When the Slack account is authenticated, we provision the Slack workspace which is represented by the `status` field.
    The provisioning is asynchronous and is taken care of by the worker. During provisioning, we ensure that we have the
    necessary rights to access the Slack workspace.
    The provisioning pipeline also syncs the data from Slack to our database. This pipeline consists of various tasks as required.
    Once the provisioning is complete, the status is set to 'ready'.

    'ready' is the state when the Slack workspace is ready to be used.
    'deactivated' is the state when the Slack workspace is deactivated or the OAuth is deleted.

    'sync_status' is used to track the sync status of the Slack workspace. Since we heavily rely on Slack APIs to sync the data,
    we need to keep track of the sync status of the Slack workspace.
    """

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
            return False
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
            return False
        return self.workspace_id == other.workspace_id and self.ref == other.ref

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
    def sync_status_aborted() -> str:
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
    """
    Represents a Slack Bot added to a Slack Workspace.

    We are using a convention of naming Slack based data model `_id` as `_ref`
    to avoid confusion with the database `id` field.

    Important fields:
    - bot_user_ref - represents the `bot_user_id` from Slack API
    - app_ref - represents the `app_id` from Slack API
    - bot_id - represents PK not to be confused with `bot_ref`
    - bot_ref - represents the `bot_id` from Slack API

    Every Slack Bot added has 1:1 mapping with Slack Workspace. There cannot be
    multiple Slack Bots for a single Slack Workspace.
    """

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
            return False
        return (
            self.slack_workspace == other.slack_workspace
            and self.bot_id == other.bot_id
        )

    def equals_by_bot_user_ref(self, other: object) -> bool:
        if not isinstance(other, SlackBot):
            return False
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


class SlackChannel(AbstractEntity):
    def __init__(
        self,
        slack_workspace_ref: str,
        channel_ref: str,
        is_channel: bool,
        is_ext_shared: bool,
        is_general: bool,
        is_group: bool,
        is_im: bool,
        is_member: bool,
        is_mpim: bool,
        is_org_shared: bool,
        is_pending_ext_shared: bool,
        is_private: bool,
        is_shared: bool,
        name: str,
        name_normalized: str,
        created: int,
        updated: int,
        channel_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        synced_at: datetime | None = None,
        status: SlackChannelStatus | str = SlackChannelStatus.MUTE,
    ):
        self.slack_workspace_ref = slack_workspace_ref
        self.channel_id = channel_id
        self.channel_ref = channel_ref
        self.is_channel = is_channel
        self.is_ext_shared = is_ext_shared
        self.is_general = is_general
        self.is_group = is_group
        self.is_im = is_im
        self.is_member = is_member
        self.is_mpim = is_mpim
        self.is_org_shared = is_org_shared
        self.is_pending_ext_shared = is_pending_ext_shared
        self.is_private = is_private
        self.is_shared = is_shared
        self.name = name
        self.name_normalized = name_normalized
        self.created = created
        self.updated = updated
        self.created_at = created_at
        self.updated_at = updated_at
        self.synced_at = synced_at

        if isinstance(status, str):
            status = SlackChannelStatus(status)

        assert isinstance(status, SlackChannelStatus)
        self._status: SlackChannelStatus = status

    @property
    def status(self) -> str:
        return self._status.value

    @status.setter
    def status(self, status: SlackChannelStatus | str) -> None:
        if isinstance(status, str):
            status = SlackChannelStatus(status)
        self._status = status

    @property
    def is_muted(self) -> bool:
        return self._status == SlackChannelStatus.MUTE

    @property
    def is_listening(self) -> bool:
        return self._status == SlackChannelStatus.LISTEN

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackChannel):
            return False
        return (
            self.slack_workspace_ref == other.slack_workspace_ref
            and self.channel_ref == other.channel_ref
        )

    def equals_by_channel_ref(self, other: object) -> bool:
        if not isinstance(other, SlackChannel):
            return False
        return (
            self.slack_workspace_ref == other.slack_workspace_ref
            and self.channel_ref == other.channel_ref
        )

    def __repr__(self) -> str:
        return f"""SlackChannelSync(
            slack_workspace_ref={self.slack_workspace_ref},
            channel_id={self.channel_id},
            channel_ref={self.channel_ref},
            name={self.name},
            name_normalized={self.name_normalized},
            created_at={self.created_at},
            updated_at={self.updated_at},
            synced_at={self.synced_at},
            status={self.status},
        )"""

    @staticmethod
    def status_mute() -> str:
        return SlackChannelStatus.MUTE.value

    @staticmethod
    def status_listen() -> str:
        return SlackChannelStatus.LISTEN.value

    @classmethod
    def from_dict(cls, slack_workspace_ref: str, values: dict) -> "SlackChannel":
        return cls(
            slack_workspace_ref=slack_workspace_ref,
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
            synced_at=cls._parse_datetime(values.get("synced_at", None)),
            created_at=cls._parse_datetime(values.get("created_at", None)),
            updated_at=cls._parse_datetime(values.get("updated_at", None)),
        )

    def to_dict(self) -> dict:
        return {
            "slack_workspace_ref": self.slack_workspace_ref,
            "channel_id": self.channel_id,
            "id": self.channel_ref,
            "is_channel": self.is_channel,
            "is_ext_shared": self.is_ext_shared,
            "is_general": self.is_general,
            "is_group": self.is_group,
            "is_im": self.is_im,
            "is_member": self.is_member,
            "is_mpim": self.is_mpim,
            "is_org_shared": self.is_org_shared,
            "is_pending_ext_shared": self.is_pending_ext_shared,
            "is_private": self.is_private,
            "is_shared": self.is_shared,
            "name": self.name,
            "name_normalized": self.name_normalized,
            "created": self.created,
            "updated": self.updated,
            "status": self.status,
            "synced_at": self.synced_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SlackChannelConfig(AbstractEntity):
    pass
