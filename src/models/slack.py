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
