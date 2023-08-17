from enum import Enum


class UserType(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


class User:
    def __init__(self, user_id: str, email: str) -> None:
        self.user_id = user_id
        self.email = email


class Requester:
    def __init__(self, requester_id: str, email: str) -> None:
        self.requester_id = requester_id
        self.email = email


class Assignee:
    def __init__(self, assignee_id: str, email: str) -> None:
        self.assignee_id = assignee_id
        self.email = email


class Issue:
    def __init__(self, requester: Requester, title: str, body: str) -> None:
        self.issue_id = None
        self.requester = requester
        self.title = title
        self.body = body
        self.assignee = None

    def __eq__(self, other: object) -> bool:
        if self.issue_id is None:  # cannot be compared without identifier
            return False
        if not isinstance(other, Issue):
            return False
        return self.issue_id == other.issue_id

    def assign(self, assignee: Assignee):
        self.assignee = assignee
