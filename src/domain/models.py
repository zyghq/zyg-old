import abc
from datetime import datetime
from enum import Enum
from typing import List

from attrs import define, field

from src.domain.exceptions import SlackChannelReferenceValueError, TenantValueError


class AbstractEntity(abc.ABC):
    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


class AbstractValueObject:
    pass


@define(frozen=True)
class TenantContext(AbstractValueObject):
    """
    Represents a tenant context.

    Attributes:
        tenant_id (str): The ID of the tenant.
        name (str): The name of the tenant.
        slack_team_ref (str): The reference to the Slack team.

    Note: This is different from `Tenant` entity. This is a value object,
    to be used for tenant context to pass around as a value with no business logic.
    """

    tenant_id: str
    name: str = field(eq=False)
    slack_team_ref: str


class Tenant(AbstractEntity):
    def __init__(self, tenant_id: str | None, name: str, slack_team_ref: str) -> None:
        self.tenant_id = tenant_id
        self.name = name
        self.slack_team_ref = slack_team_ref

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

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slack_team_ref": self.slack_team_ref,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tenant":
        return cls(
            tenant_id=data.get("tenant_id"),
            name=data.get("name"),
            slack_team_ref=data.get("slack_team_ref"),
        )

    def build_context(self) -> TenantContext:
        return TenantContext(
            tenant_id=self.tenant_id,
            name=self.name,
            slack_team_ref=self.slack_team_ref,
        )


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


class BaseEvent:
    def __init__(
        self,
        tenant_id: str,
        slack_event_ref: str,
        inner_event_type: str,
    ) -> None:
        self.tenant_id = tenant_id
        self.slack_event_ref = slack_event_ref
        self.inner_event_type = inner_event_type

    def to_dict() -> dict:
        raise NotImplementedError


class EventChannelMessage(BaseEvent):
    subscribed_event = "message.channels"

    def __init__(
        self,
        tenant_id: str,
        slack_event_ref: str,
        slack_channel_ref: str,
        inner_event_type: str,
        event: dict,
    ) -> None:
        super().__init__(tenant_id, slack_event_ref, inner_event_type)
        self.slack_channel_ref = slack_channel_ref

        self.message = self._parse(event=event)

    def _parse(self, event: dict) -> None:
        # XXX(@sanchitrk): update this based on testing.
        parsed_event = {}
        ts = event.get("ts", None)
        body = event.get("text", None)
        slack_user_ref = event.get("user", None)
        client_msg_id = event.get("client_msg_id", None)

        assert ts is not None
        assert body is not None
        assert slack_user_ref is not None
        assert client_msg_id is not None

        parsed_event["ts"] = ts
        parsed_event["body"] = body
        parsed_event["slack_user_ref"] = slack_user_ref
        parsed_event["client_msg_id"] = client_msg_id
        return parsed_event

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "slack_event_ref": self.slack_event_ref,
            "slack_channel_ref": self.slack_channel_ref,
            "inner_event_type": self.inner_event_type,
            "message": self.message,
            "subscribed_event": self.subscribed_event,
        }

    def __repr__(self) -> str:
        return f"""EventChannelMessage(
            tenant_id={self.tenant_id},
            slack_event_ref={self.slack_event_ref},
            slack_channel_ref={self.slack_channel_ref},
            inner_event_type={self.inner_event_type},
            subscribed_event={self.subscribed_event},
        )"""


class SlackEvent(AbstractEntity):
    """
    `subscribed_events` - are list of events that we are subscribed to in Slack.
    """

    subscribed_events = ("message.channels",)

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
        self.payload = payload  # slack event payload

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
    def from_payload(
        cls, tenant_id: str, event_id: str | None, payload: dict
    ) -> "SlackEvent":
        slack_event_ref = payload.get("event_id", None)  # from slack `event_id`
        slack_event_ref = cls._clean_slack_event_ref(slack_event_ref)
        if not slack_event_ref:
            raise ValueError(
                "slack event reference (from slack `event_id`) is required"
            )
        event_ts = payload.get("event_time", None)
        if not event_ts:
            raise ValueError(
                "slack event time stamp (from slack `event_time`) is required"
            )

        payload_event = payload.get("event", None)
        if not payload_event:
            raise ValueError("slack inner event cannot be empty")

        slack_event = cls(
            tenant_id=tenant_id,
            event_id=event_id,
            slack_event_ref=slack_event_ref,
            event_ts=event_ts,
            payload=payload,
        )

        event = slack_event.build_event(event=payload_event)
        slack_event.event = event
        return slack_event

    def _parse_to_subscribed_event(self, event: dict) -> str:
        """
        Parses the inner event type to find the subscribed event.
        Returns the subscribed event name as subscribed.

        If we are not able to find the subscribed event, we raise an error.

        Note: Add support for more subscribed events.
        """
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
        raise ValueError("event type is not supported or subscribed")

    def build_event(self, event: dict) -> None:
        """
        First we parse the event to find the subscribed event,
        and make sure it is in subscribed events - we dont want to end up
        with an event that we are not subscribed to.

        Then we build the event based on the subscribed event.
        """
        subscribed_event = self._parse_to_subscribed_event(event=event)
        if subscribed_event not in self.subscribed_events:
            raise ValueError(
                "subscribed event not added to subscribed events may be forgotten?"
            )

        if subscribed_event == "message.channels":
            channel = event.get("channel", None)
            inner_event_type = event.get("type", "n/a")
            return EventChannelMessage(
                tenant_id=self.tenant_id,
                slack_event_ref=self.slack_event_ref,
                slack_channel_ref=channel,
                inner_event_type=inner_event_type,
                event=event,
            )
        raise ValueError("cannot build event for unknown event type")

    @classmethod
    def is_event_subscribed(cls, name):
        return name in cls.subscribed_events

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

    def to_dict(self):
        if isinstance(self.event, BaseEvent):
            event = self.event.to_dict()
        else:
            event = None
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "slack_event_ref": self.slack_event_ref,
            "inner_event_type": self.inner_event_type,
            "event": event,
            "event_ts": self.event_ts,
            "api_app_id": self.api_app_id,
            "token": self.token,
            "payload": self.payload,
            "is_ack": self.is_ack,
        }

    def get_message(self) -> dict | None:
        if isinstance(self.event, EventChannelMessage):
            return self.event.message
        return None


@define(frozen=True)
class InSyncSlackChannelItem(AbstractValueObject):
    """
    Represents a Slack conversation item, after succesful API call.
    We call it Slack Channel for our understandings.
    Attrs:
        as defined in https://api.slack.com/types/conversation
    """

    tenant_id: str
    context_team_id: str
    created: int = field(eq=False)
    creator: str
    id: str
    is_archived: bool
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
    name: str = field(eq=False)
    name_normalized: str = field(eq=False)
    num_members: int = field(eq=False)
    parent_conversation: str | None = field(eq=False)
    pending_connected_team_ids: List[str] = field(eq=False)
    pending_shared: List[str] = field(eq=False)
    previous_names: List[str] = field(eq=False)
    purpose: dict[str, str] = field(eq=False)
    shared_team_ids: List[str] = field(eq=False)
    topic: dict[str, str] = field(eq=False)
    unlinked: int = field(eq=False)
    updated: int = field(eq=False)

    updated_at: datetime | None = None
    created_at: datetime | None = None

    @classmethod
    def from_dict(cls, tenant_id, data: dict) -> "InSyncSlackChannelItem":
        return cls(
            tenant_id=tenant_id,
            context_team_id=data.get("context_team_id"),
            created=data.get("created"),
            creator=data.get("creator"),
            id=data.get("id"),
            is_archived=data.get("is_archived"),
            is_channel=data.get("is_channel"),
            is_ext_shared=data.get("is_ext_shared"),
            is_general=data.get("is_general"),
            is_group=data.get("is_group"),
            is_im=data.get("is_im"),
            is_member=data.get("is_member"),
            is_mpim=data.get("is_mpim"),
            is_org_shared=data.get("is_org_shared"),
            is_pending_ext_shared=data.get("is_pending_ext_shared"),
            is_private=data.get("is_private"),
            is_shared=data.get("is_shared"),
            name=data.get("name"),
            name_normalized=data.get("name_normalized"),
            num_members=data.get("num_members"),
            parent_conversation=data.get("parent_conversation"),
            pending_connected_team_ids=data.get("pending_connected_team_ids"),
            pending_shared=data.get("pending_shared"),
            previous_names=data.get("previous_names"),
            purpose=data.get("purpose"),
            shared_team_ids=data.get("shared_team_ids"),
            topic=data.get("topic"),
            unlinked=data.get("unlinked"),
            updated=data.get("updated"),
        )


@define(frozen=True)
class TriageSlackChannel(AbstractValueObject):
    tenant_id: str
    slack_channel_ref: str
    slack_channel_name: str


class LinkedSlackChannel(AbstractEntity):
    def __init__(
        self,
        tenant_id: str,
        linked_slack_channel_id: str | None,
        slack_channel_ref: str,
        slack_channel_name: str,
    ) -> None:
        self.tenant_id = tenant_id
        self.linked_slack_channel_id = linked_slack_channel_id
        self.slack_channel_ref = slack_channel_ref
        self.slack_channel_name = slack_channel_name

        # TODO: shall we make it global compulsory to add triage channel?
        self.triage_channel: TriageSlackChannel | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LinkedSlackChannel):
            return False
        return (
            self.tenant_id == other.tenant_id
            and self.linked_slack_channel_id == other.linked_slack_channel_id
            and self.slack_channel_ref == other.slack_channel_ref
        )

    def __repr__(self) -> str:
        return f"""LinkedSlackChannel(
            tenant_id={self.tenant_id},
            linked_slack_channel_id={self.linked_slack_channel_id},
            slack_channel_ref={self.slack_channel_ref},
            slack_channel_name={self.slack_channel_name}
        )"""

    def add_triage_channel(self, triage_channel: TriageSlackChannel) -> None:
        """
        Checks if it is of the same tenant and linked slack channel ref
        is not same as triage's slack channel ref.
        """
        if self.tenant_id != triage_channel.tenant_id:
            raise TenantValueError(
                "cannot link triage channel of different tenant - this cannot happen!"
            )
        if self.slack_channel_ref == triage_channel.slack_channel_ref:
            raise SlackChannelReferenceValueError(
                "cannot add triage channel for the same linked slack channel"
            )
        self.triage_channel = triage_channel


class IssueStatus(Enum):
    OPEN = "open"
    INPROGRESS = "inprogress"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    DUPLICATE = "duplicate"


class IssuePriority(Enum):
    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class Issue(AbstractEntity):
    def __init__(
        self,
        tenant_id: str,
        issue_id: str | None,
        issue_number: int | None,
        body: str,
        status: IssueStatus | None | str = IssueStatus.OPEN,
        priority: IssuePriority | None | int = IssuePriority.NO_PRIORITY,
    ) -> None:
        self.tenant_id = tenant_id
        self.issue_id = issue_id
        self.body = body

        if status is None:
            status = IssueStatus.OPEN
        if priority is None:
            priority = IssuePriority.NO_PRIORITY

        if isinstance(status, str):
            status = IssueStatus(status)
        if isinstance(priority, int):
            priority = IssuePriority(priority)

        assert isinstance(status, IssueStatus)
        assert isinstance(priority, IssuePriority)

        self._status = status
        self._priority = priority

        self.issue_number = issue_number

        self._tags = set()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Issue):
            return False
        return self.issue_id == other.issue_id

    def equals_by_issue_number(self, other: object) -> bool:
        if self.issue_number is None:
            return False
        if not isinstance(other, Issue):
            return False
        return (
            self.tenant_id == self.tenant_id and self.issue_number == other.issue_number
        )

    def __repr__(self) -> str:
        return f"""Issue(
            tenant_id={self.tenant_id},
            issue_id={self.issue_id},
            issue_number={self.issue_number},
            body={self.body[:32]}...,
            status={self.status},
            priority={self.priority},
        )"""

    def add_tag(self, tag: str) -> None:
        self._tags.add(tag)

    def set_issue_number(self, issue_number: str) -> None:
        self.issue_number = issue_number

    @property
    def tags(self) -> List[str]:
        return list(self._tags)

    @tags.setter
    def tags(self, tags: List[str] | None) -> None:
        if tags is None:
            self._tags = set()
            return
        self._tags = set([str(t).lower() for t in tags])

    @property
    def status(self) -> str:
        if self._status is None:
            return IssueStatus.OPEN.value
        return self._status.value

    @status.setter
    def status(self, status: str) -> None:
        self._status = IssueStatus(status)

    @property
    def priority(self) -> int:
        if self._priority is None:
            return IssuePriority.NO_PRIORITY.value
        return self._priority.value

    @priority.setter
    def priority(self, priority: int) -> None:
        self._priority = IssuePriority(priority)

    @staticmethod
    def default_status() -> str:
        return IssueStatus.OPEN.value

    @staticmethod
    def default_priority() -> int:
        return IssuePriority.NO_PRIORITY.value
