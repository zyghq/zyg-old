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

    def to_dict(self) -> dict:
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
    """
    Enum class representing the different roles a member can have in an account.
    """

    PRIMARY = "primary"
    OWNER = "owner"
    ADMIN = "administrator"
    MEMBER = "member"


class Member(AbstractEntity):
    """
    Represents a member of an account in a workspace.

    Attributes:
        workspace (Workspace): The workspace the member belongs to.
        account (Account): The account the member belongs to.
        member_id (str, optional): The ID of the member. Defaults to None.
        slug (str, optional): The slug of the member. Defaults to None.
        role (MemberRole, optional): The role of the member. Defaults to MemberRole.MEMBER.
        created_at (datetime, optional): The datetime when the member was created. Defaults to None.
        updated_at (datetime, optional): The datetime when the member was last updated. Defaults to None.
    """

    def __init__(
        self,
        workspace: Workspace,
        account: Account,
        member_id: str | None = None,
        slug: str | None = None,
        role: MemberRole = MemberRole.MEMBER,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.workspace = workspace
        self.account = account
        self.member_id = member_id
        self.slug = slug
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Member):
            return False
        return self.workspace == other.workspace and self.member_id == other.member_id

    def equals_by_slug(self, other: object) -> bool:
        if not isinstance(other, Member):
            return False
        return self.workspace == other.workspace and self.slug == other.slug

    def __repr__(self) -> str:
        return f"""Member(
            workspace_id={self.workspace.workspace_id},
            account_id={self.account.account_id},
            member_id={self.member_id},
            slug={self.slug},
            role={self.role},
            created_at={self.created_at},
            updated_at={self.updated_at},
        )"""

    def to_dict(self) -> dict:
        workspace_id = self.workspace.workspace_id if self.workspace else None
        account_id = self.account.account_id if self.account else None
        return {
            "workspace_id": workspace_id,
            "account_id": account_id,
            "member_id": self.member_id,
            "slug": self.slug,
            "role": self.role,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def get_role_primary(cls):
        return MemberRole.PRIMARY

    @classmethod
    def get_role_owner(cls):
        return MemberRole.OWNER

    @classmethod
    def get_role_admin(cls):
        return MemberRole.ADMIN

    @classmethod
    def get_role_member(cls):
        return MemberRole.MEMBER

    @property
    def is_role_primary(self) -> bool:
        return self.role == MemberRole.PRIMARY

    @property
    def is_role_owner(self) -> bool:
        return self.role == MemberRole.OWNER

    @property
    def is_role_admin(self) -> bool:
        return self.role == MemberRole.ADMIN

    @property
    def is_role_member(self) -> bool:
        return self.role == MemberRole.MEMBER
