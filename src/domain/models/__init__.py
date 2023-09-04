import abc
from enum import Enum

from attrs import define, field


class AbstractEntity(abc.ABC):
    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


class AbstractValueObject:
    pass


# deprecate
class SlackCallbackEvent(AbstractEntity):
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


class Tenant(AbstractEntity):
    def __init__(self, tenant_id: str | None, name: str) -> None:
        self.tenant_id = tenant_id
        self.name = name
        self.slack_team_ref: str | None = None  # Slack team reference id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tenant):
            return False
        return self.tenant_id == other.tenant_id

    def __repr__(self) -> str:
        return f"""Tenant(
            tenant_id={self.tenant_id},
            name={self.name},
            slack_team_ref={self.slack_team_ref}
        )"""

    def _clean_slack_team_ref(self, team_ref: str) -> str:
        return team_ref.strip().lower()

    def set_slack_team_ref(self, team_ref: str | None) -> None:
        if team_ref is None:
            self.slack_team_ref = None
            return
        self.slack_team_ref = self._clean_slack_team_ref(team_ref)


class UserRole(Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"


class User(AbstractEntity):
    def __init__(
        self,
        tenant_id: str,
        user_id: str | None,
        name: str | None,
        role: UserRole.MEMBER,
    ) -> None:
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.name = name
        self.role = role

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return (self.tenant_id == other.tenant_id) and (self.user_id == other.user_id)

    def __repr__(self) -> str:
        return f"""User(
            tenant_id={self.tenant_id},
            user_id={self.user_id},
            name={self.name},
            role={self.role.value}
        )"""


@define(kw_only=True)
class BaseEvent(AbstractValueObject):
    """
    Represents a base event.

    Attributes:
        tenant_id (str): The ID of the tenant.
        event_id (str): The ID of the event.
        event_ts (int): The timestamp of the event.
        event (dict | None): The event data, if any.
        inner_event_type (str): The inner event type.
    """

    tenant_id: str
    event_id: str
    event_ts: int = field(eq=False)
    event: dict | None = field(default=None, eq=False)
    inner_event_type: str = field(eq=False)


@define
class EventChannelMessage(BaseEvent):
    """
    Represents a message channel event.

    Then naming convention follows reverse of the subscribed event name.
    With prefix by `Event`

    For example here we have `message.channels` subscribed event, so we have
    `EventChannelMessage` as the event name.

    Attributes:
        subscribed_event (str): The name of the subscribed event.
        slack_team_ref (str): The reference to the Slack team.
        slack_channel_ref (str): The reference to the Slack channel.
    """

    slack_event_ref: str
    slack_channel_ref: str

    # subscribed_event: str = "message.channels"
    subscribed_event: str = field(default="message.channels", eq=False)


class SlackEvent(AbstractEntity):
    def __init__(
        self,
        tenant_id: str,
        event_id: str | None,
        slack_event_ref: str,
        event_ts: int,
        payload: dict,
        is_ack: bool = False,
    ) -> None:
        self.tenant_id = tenant_id
        self.event_id = event_id
        self.slack_event_ref = slack_event_ref
        self.event_ts = event_ts
        self.payload = payload

        self.is_ack = is_ack

        self.event: BaseEvent | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlackEvent):
            return False
        return self.event_id == other.event_id

    def equals_by_slack_event_ref(self, other: object) -> bool:
        if not isinstance(other, SlackEvent):
            return False
        return self.slack_event_ref == other.slack_event_ref

    def __repr__(self) -> str:
        return f"""SlackEvent(
            tenant_id={self.tenant_id},
            event_id={self.event_id},
            event_ts={self.event_ts},
            slack_event_ref={self.slack_event_ref}
        )"""

    @staticmethod
    def _clean_slack_event_ref(slack_event_ref: str) -> str:
        return slack_event_ref.strip().lower()

    @classmethod
    def init_from_payload(cls, tenant_id: str, payload: dict) -> "SlackEvent":
        slack_event_ref = payload.get("event_id", None)
        slack_event_ref = cls._clean_slack_event_ref(slack_event_ref)
        if not slack_event_ref:
            raise ValueError("slack event reference (slack `event_id`) is required")
        event_ts = payload.get("event_time", None)
        if not event_ts:
            raise ValueError("slack event time stamp (slack `event_time`) is required")

        slack_event = cls(
            tenant_id=tenant_id,
            event_id=None,
            slack_event_ref=slack_event_ref,
            event_ts=event_ts,
            payload=payload,
        )
        payload_event = payload.get("event", {})
        event = slack_event.make_event(event=payload_event)
        slack_event.set_event(event=event)
        return slack_event

    def _parse_to_subscribed_event(self, event: dict) -> None:
        event_type = event.get("type", None)
        if not event_type:
            raise ValueError("event type is required")
        if event_type == "message":
            # follow the path to `message.*`
            channel_type = event.get("channel_type", None)
            if not channel_type:
                raise ValueError("channel type is required")
            if channel_type == "channel":
                # follow the path `message.channels`
                return "message.channels"
        raise ValueError("event type is not supported")

    def make_event(self, event: dict) -> None:
        subscribed_event = self._parse_to_subscribed_event(event=event)
        if subscribed_event == "message.channels":
            channel = event.get("channel", None)
            inner_event_type = event.get("type", "n/a")
            return EventChannelMessage(
                tenant_id=self.tenant_id,
                event_id=self.event_id,
                slack_event_ref=self.slack_event_ref,
                slack_channel_ref=channel,
                event_ts=self.event_ts,
                event=event,
                inner_event_type=inner_event_type,
            )
        raise ValueError("cannot make event for unsupported event type")

    def set_event(self, event: AbstractValueObject | None) -> None:
        if event is None:
            self.event = None
            return
        self.event = event

    @property
    def inner_event_type(self) -> str:
        if self.event is None:
            raise ValueError(
                "cannot find `inner_event_type` as event is None. "
                "try setting event first with `set_event` method. "
                "before that you need to invoke `make_event` method first, "
                "so that we can parse the event to detect the slack event type"
            )
        return self.event.inner_event_type

    @property
    def api_app_id(self) -> str | None:
        api_app_id = self.payload.get("api_app_id", None)
        return api_app_id

    @property
    def token(self) -> str | None:
        token = self.payload.get("token", None)
        return token
