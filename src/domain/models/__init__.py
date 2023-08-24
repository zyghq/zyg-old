import abc
from enum import Enum


class UserRole(Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"


class AbstractModel(abc.ABC):
    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


class User(AbstractModel):
    def __init__(
        self, user_id: str | None, name: str | None, role: UserRole.MEMBER
    ) -> None:
        self.user_id = user_id
        self.name = name
        self.role = role

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id

    def __repr__(self) -> str:
        return f"""User(
            user_id={self.user_id},
            name={self.name},
            role={self.role}
        )"""


class SlackCallbackEvent(AbstractModel):
    """
    Represents a Slack callback event.

    Attributes:
        event_id (str): The unique identifier for the event.
        team_id (str): The unique identifier for the team.
        event_type (str): The type of event.
        event (dict): The event payload.
        event_ts (int, optional): The event time stamp from Slack.
        metadata (dict, optional): Other metadata from Slack.
    """

    def __init__(
        self,
        event_id: str,
        team_id: str,
        event_type: str,
        event: dict,
        event_ts: int,
        metadata: dict | None = None,
        is_ack: bool = False,
    ) -> None:
        self.event_id = event_id
        self.team_id = team_id
        self.event_type = event_type
        self.event = event
        self.event_ts = event_ts  # event time stamp from Slack
        self.metadata = metadata  # other metadata from Slack
        self.is_ack = is_ack  # whether the event was acknowledged

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackCallbackEvent):
            return False
        return self.event_id == other.event_id

    def __repr__(self) -> str:
        return f"""SlackCallbackEvent(
                event_id={self.event_id},
                team_id={self.team_id},
                event_type={self.event_type}
            )"""


class SlackChannel(AbstractModel):
    """
    Represents a Slack channel.

    Attributes:
        channel_id (str): The unique identifier for the channel.
    """

    def __init__(
        self, channel_id: str | None, name: str | None, channel_type: str
    ) -> None:
        self.channel_id = channel_id
        self.name = name
        self.channel_type = channel_type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackChannel):
            return False
        return self.channel_id == other.channel_id

    def __repr__(self) -> str:
        return f"SlackChannel(channel_id={self.channel_id})"


class Inbox(AbstractModel):
    """
    Represents an inbox object that can be linked to a Slack channel.

    Attributes:
        inbox_id (str): Unique identifier for the inbox.
        name (str): Required name of the inbox.
        description (str, optional): description of the inbox.
        slack_channel (SlackChannel, optional): Slack channel linked to the inbox.
    """

    def __init__(
        self,
        inbox_id: str | None,
        name: str,
        description: str | None,
        slack_channel: SlackChannel | None,
    ) -> None:
        self.inbox_id = inbox_id  # unique identifier
        self.name = name  # required
        self.description = description  # optional
        self.slack_channel = slack_channel  # linked Slack channel

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Inbox):
            return False
        return self.inbox_id == other.inbox_id

    def __repr__(self) -> str:
        return f"""Inbox(
                inbox_id={self.inbox_id},
                name={self.name},
                description={self.description[: 64]}
            )"""

    def link_channel(self, slack_channel: SlackChannel) -> None:
        self.slack_channel = slack_channel


class Issue(AbstractModel):
    def __init__(
        self,
        issue_id: str | None,
        inbox_id: str,
        requester_id: str,
        body: str,
        title: str | None,
    ) -> None:
        self.issue_id = issue_id
        self.inbox_id = inbox_id
        self.requester_id = requester_id
        self.body = body
        self._title = title

    @property
    def title(self) -> str:
        if self._title is None:
            return f"{self.body[:64]}..."
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Issue):
            return False
        return self.issue_id == other.issue_id

    def __hash__(self) -> int:
        return hash(self.issue_id)

    def __repr__(self) -> str:
        return f"""Issue(
            issue_id={self.issue_id},
            inbox_id={self.inbox_id},
            requester_id={self.requester_id},
            title={self.title},
            body={self.body[: 64]}
        )"""
