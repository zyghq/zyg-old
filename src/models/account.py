from datetime import datetime
from enum import Enum

from .base import AbstractEntity


class Account(AbstractEntity):
    """
    Represents Auth User Account.
    """

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

    @classmethod
    def from_dict(cls, values: dict) -> "Account":
        created_at = cls._parse_datetime(values.get("created_at", None))
        updated_at = cls._parse_datetime(values.get("updated_at", None))
        return cls(
            account_id=values.get("account_id"),
            provider=values.get("provider"),
            auth_user_id=values.get("auth_user_id"),
            email=values.get("email"),
            name=values.get("name"),
            created_at=created_at,
            updated_at=updated_at,
        )


class Workspace(AbstractEntity):
    def __init__(
        self,
        account_id: str,
        workspace_id: str | None,
        name: str,
        slug: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.account_id = account_id
        self.workspace_id = workspace_id
        self.name = name
        self.slug = slug
        self.created_at = created_at
        self.updated_at = updated_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workspace):
            return False
        return (
            self.account_id == other.account_id
            and self.workspace_id == other.workspace_id
        )

    def equals_by_slug(self, other: object) -> bool:
        if not isinstance(other, Workspace):
            return False
        return self.account_id == other.account_id and self.slug == other.slug

    def __repr__(self) -> str:
        return f"""Workspace(
            account_id={self.account_id},
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

    @classmethod
    def from_dict(cls, account_id: str, values: dict) -> "Workspace":
        created_at = cls._parse_datetime(values.get("created_at", None))
        updated_at = cls._parse_datetime(values.get("updated_at", None))
        return cls(
            account_id=account_id,
            workspace_id=values.get("workspace_id"),
            slug=values.get("slug"),
            name=values.get("name"),
            created_at=created_at,
            updated_at=updated_at,
        )


class MemberRole(Enum):
    """
    Enum class representing the different roles a member can have in an Account.
    """

    PRIMARY = "primary"
    OWNER = "owner"
    ADMIN = "administrator"
    MEMBER = "member"


class Member(AbstractEntity):
    """
    Represents a Member of an Account in a Workspace.
    """

    def __init__(
        self,
        workspace_id: str,
        account_id: str,
        member_id: str | None = None,
        slug: str | None = None,
        role: MemberRole | None | str = MemberRole.MEMBER,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.workspace_id = workspace_id
        self.account_id = account_id
        self.member_id = member_id
        self.slug = slug
        self.created_at = created_at
        self.updated_at = updated_at

        if role is None:
            role = MemberRole.MEMBER
        elif isinstance(role, str):
            role = MemberRole(role)

        assert isinstance(role, MemberRole)

        self._role = role

    @property
    def role(self) -> str:
        if self._role is None:
            return MemberRole.MEMBER.value
        return self._role.value

    @role.setter
    def role(self, role: MemberRole | str) -> None:
        if isinstance(role, str):
            role = MemberRole(role)
        self._role = role

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Member):
            return False
        return (
            self.workspace_id == other.workspace_id
            and self.member_id == other.member_id
        )

    def equals_by_slug(self, other: object) -> bool:
        if not isinstance(other, Member):
            return False
        return self.workspace_id == other.workspace_id and self.slug == other.slug

    def __repr__(self) -> str:
        return f"""Member(
            workspace_id={self.workspace_id},
            account_id={self.account_id},
            member_id={self.member_id},
            slug={self.slug},
            role={self.role},
            created_at={self.created_at},
            updated_at={self.updated_at},
        )"""

    def to_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "account_id": self.account_id,
            "member_id": self.member_id,
            "slug": self.slug,
            "role": self.role,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def get_role_primary() -> str:
        return MemberRole.PRIMARY.value

    @staticmethod
    def get_role_owner() -> str:
        return MemberRole.OWNER.value

    @staticmethod
    def get_role_admin() -> str:
        return MemberRole.ADMIN.value

    @staticmethod
    def get_role_member() -> str:
        return MemberRole.MEMBER.value

    @property
    def is_role_primary(self) -> bool:
        return self._role == MemberRole.PRIMARY

    @property
    def is_role_owner(self) -> bool:
        return self._role == MemberRole.OWNER

    @property
    def is_role_admin(self) -> bool:
        return self._role == MemberRole.ADMIN

    @property
    def is_role_member(self) -> bool:
        return self._role == MemberRole.MEMBER
