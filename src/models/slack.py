from .base import AbstractEntity
from .account import Workspace


class SlackWorkspace(AbstractEntity):
    def __init__(self, workspace: Workspace, ref: str, url: str, name: str) -> None:
        self.workspace = workspace
        self.ref = ref
        self.url = url
        self.name = name

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


class SlackBot(AbstractEntity):
    def __init__(
        self,
        workspace: SlackWorkspace,
        bot_id: str,
        bot_user_ref: str,
        app_ref: str,
        scope: str,
        access_token: str,
    ):
        self.workspace = workspace
        self.bot_id = bot_id
        self.bot_user_ref = bot_user_ref
        self.app_ref = app_ref
        self.scope = scope
        self.access_token = access_token

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackBot):
            return NotImplemented
        return self.workspace == other.workspace and self.bot_id == other.bot_id

    def equals_by_bot_user_ref(self, other: object) -> bool:
        if not isinstance(other, SlackBot):
            return NotImplemented
        return (
            self.workspace == other.workspace
            and self.bot_user_ref == other.bot_user_ref
        )

    def __repr__(self) -> str:
        return f"""SlackBot(
            workspace={self.workspace},
            bot_id={self.bot_id},
            bot_user_ref={self.bot_user_ref},
            app_ref={self.app_ref},
        )"""
