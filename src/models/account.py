from datetime import datetime

from .base import AbstractEntity


class Account(AbstractEntity):
    def __init__(
        self,
        account_id: str | None,
        provider: str,
        auth_user_id: str,
        name: str,
        created_at: datetime | None,
        updated_at: datetime | None,
    ):
        self.account_id = account_id
        self.provider = provider
        self.auth_user_id = auth_user_id
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
            name={self.name},
            created_at={self.created_at},
            updated_at={self.updated_at},
        )"""

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "provider": self.provider,
            "auth_user_id": self.auth_user_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Workspace(AbstractEntity):
    def __init__(
        self,
        workspace_id: str,
        name: str,
        created_at: datetime | None,
        updated_at: datetime | None,
    ):
        self.workspace_id = workspace_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

        self.logo_url = None

        self.account: Account | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workspace):
            return False
        return self.account == other.account and self.workspace_id == other.workspace_id

    def __repr__(self) -> str:
        return f"""Workspace(
            account_id={self.account},
            workspace_id={self.workspace_id},
            name={self.name},
            created_at={self.created_at},
            updated_at={self.updated_at},
        )"""

    def to_dict(self):
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def add_account(self, account: Account):
        self.account = account

    def add_logo_url(self, logo_url: str):
        self.logo_url = logo_url
