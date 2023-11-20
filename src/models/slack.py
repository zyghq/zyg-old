from enum import Enum

from .account import Workspace
from .base import AbstractEntity


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
        status: SlackWorkspaceStatus = SlackWorkspaceStatus.PROVISIONING,
    ) -> None:
        self.workspace = workspace
        self.ref = ref
        self.url = url
        self.name = name

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
        )"""

    def to_dict(self) -> dict[str, str]:
        return {
            "workspace": self.workspace.to_dict(),
            "ref": self.ref,
            "url": self.url,
            "name": self.name,
        }

    def equals_by_ref(self, other: object) -> bool:
        if not isinstance(other, SlackWorkspace):
            return NotImplemented
        return self.ref == other.ref

    @classmethod
    def get_status_provisioning(cls) -> SlackWorkspaceStatus:
        return SlackWorkspaceStatus.PROVISIONING

    @classmethod
    def get_status_ready(cls) -> SlackWorkspaceStatus:
        return SlackWorkspaceStatus.READY

    @classmethod
    def get_status_deactivated(cls) -> SlackWorkspaceStatus:
        return SlackWorkspaceStatus.DEACTIVATED

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

    def to_dict(self) -> dict:
        return {
            "bot_id": self.bot_id,
            "bot_user_ref": self.bot_user_ref,
            "app_ref": self.app_ref,
        }
