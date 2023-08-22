import abc


class AbstractModel(abc.ABC):
    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


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
        self, event_id: str, team_id: str, event_type: str, event: dict, event_ts: int
    ) -> None:
        self.event_id: str = event_id
        self.team_id: str = team_id
        self.event_type: str = event_type
        self.event: dict = event
        self.event_ts: int = event_ts  # event time stamp from Slack
        self.metadata: dict | None = None  # other metadata from Slack

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackCallbackEvent):
            return False
        return self.event_id == other.event_id

    def __repr__(self) -> str:
        return f"SlackCallbackEvent(event_id={self.event_id}, team_id={self.team_id}, event_type={self.event_type})"

    def set_metadata(self, metadata: dict) -> None:
        self.metadata = metadata

    def set_event_ts(self, event_ts: int) -> None:
        self.event_ts = event_ts


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
        description (str, optional): Optional description of the inbox.
        slack_channel (SlackChannel, optional): Optional Slack channel linked to the inbox.
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
        return f"Inbox(inbox_id={self.inbox_id}, name={self.name}, description={self.description[: 64]})"

    def link_channel(self, slack_channel: SlackChannel) -> None:
        self.slack_channel = slack_channel


class Issue(AbstractModel):
    def __init__(self, issue_id: str, title: str, body: str) -> None:
        self.issue_id = issue_id
        self.title = title
        self.body = body

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Issue):
            return False
        return self.issue_id == other.issue_id

    def __repr__(self) -> str:
        return f"Issue(issue_id={self.issue_id}, title={self.title}, body={self.body[: 64]})"
