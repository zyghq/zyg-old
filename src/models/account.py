from datetime import datetime
from enum import Enum

from .base import AbstractEntity


class Account(AbstractEntity):
    def __init__(
        self,
        account_id: str | None,
        provider: str,
        auth_user_id: str,
        email: str | None,
        name: str,
        created_at: datetime | None,
        updated_at: datetime | None,
    ):
        self.account_id = account_id
        self.provider = provider
        self.auth_user_id = auth_user_id
        self.email = email
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account):
            return False
        return (
            self.account_id == other.account_id
            or self.auth_user_id == other.auth_user_id
        )

    def __repr__(self) -> str:
        return f"""Account(
            account_id={self.account_id},
            provider={self.provider},
            auth_user_id={self.auth_user_id},
            email={self.email},
            name={self.name},
            created_at={self.created_at},
            updated_at={self.updated_at},
        )"""

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "provider": self.provider,
            "auth_user_id": self.auth_user_id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Workspace(AbstractEntity):
    def __init__(
        self,
        workspace_id: str | None,
        name: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.workspace_id = workspace_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

        self.slug: str | None = None
        self.account: Account | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workspace):
            return False
        return self.account == other.account and self.workspace_id == other.workspace_id

    def equals_by_slug(self, other: object) -> bool:
        if not isinstance(other, Workspace):
            return False
        return self.account == other.account and self.slug == other.slug

    def __repr__(self) -> str:
        return f"""Workspace(
            account_id={self.account},
            workspace_id={self.workspace_id},
            slug={self.slug},
            name={self.name},
            created_at={self.created_at},
            updated_at={self.updated_at},
        )"""

    def to_dict(self):
        return {
            "workspace_id": self.workspace_id,
            "slug": self.slug,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def add_account(self, account: Account):
        self.account = account

    def add_slug(self, slug: str):
        self.slug = slug


class MemberRole(Enum):
    PRIMARY = "primary"
    OWNER = "owner"
    ADMIN = "administrator"
    MEMBER = "member"


class Member(AbstractEntity):
    def __init__(
        self,
        workspace_id: str,
        account_id: str,
        email: str | None,
        role: MemberRole | str = MemberRole.MEMBER,
    ):
        pass
