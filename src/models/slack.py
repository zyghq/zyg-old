from enum import Enum

from .account import Workspace
from .base import AbstractEntity


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


class SlackWorkspace(AbstractEntity):
    def __init__(
        self,
        workspace: Workspace,
        ref: str,
        url: str,
        name: str,
        status: SlackWorkspaceStatus | None | str = SlackWorkspaceStatus.PROVISIONING,
    ) -> None:
        self.workspace = workspace
        self.ref = ref
        self.url = url
        self.name = name

        if status is None:
            status = SlackWorkspaceStatus.PROVISIONING
        if isinstance(status, str):
            status = SlackWorkspaceStatus(status)

        assert isinstance(status, SlackWorkspaceStatus)

        self._status = status

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackWorkspace):
            return NotImplemented
        return self.workspace == other.workspace and self.ref == other.ref

    def __repr__(self) -> str:
        return f"""SlackWorkspace(
            workspace={self.workspace},
            ref={self.ref},
            url={self.url},
            name={self.name},
            status={self.status},
        )"""

    def equals_by_ref(self, other: object) -> bool:
        if not isinstance(other, SlackWorkspace):
            return NotImplemented
        return self.ref == other.ref

    @classmethod
    def get_status_provisioning(cls) -> str:
        return SlackWorkspaceStatus.PROVISIONING.value

    @classmethod
    def get_status_ready(cls) -> str:
        return SlackWorkspaceStatus.READY.value

    @classmethod
    def get_status_deactivated(cls) -> str:
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

    @property
    def status(self) -> str:
        if self._status is None:
            return SlackWorkspaceStatus.PROVISIONING.value
        return self._status.value

    @status.setter
    def status(self, status: str) -> None:
        self._status = SlackWorkspaceStatus(status)

    def to_dict(self) -> dict[str, str]:
        return {
            "workspace": self.workspace.to_dict(),
            "ref": self.ref,
            "url": self.url,
            "name": self.name,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, workspace: Workspace, values: dict) -> "SlackWorkspace":
        return cls(
            workspace=workspace,
            ref=values.get("ref"),
            url=values.get("url"),
            name=values.get("name"),
            status=values.get("status"),
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
