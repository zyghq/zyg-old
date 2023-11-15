from datetime import datetime

from pydantic import BaseModel


class DBEntity(BaseModel):
    created_at: datetime | None = None  # db timestamp
    updated_at: datetime | None = None  # db timestamp


class AccountDBEntity(DBEntity):
    account_id: str | None = None  # primary key
    provider: str
    auth_user_id: str  # unique
    email: str  # unique
    name: str


class WorkspaceDBEntity(DBEntity):
    workspace_id: str | None = None  # primary key
    account_id: str
    name: str
    slug: str | None = None  # unique
