import abc
import uuid
from typing import List

import shortuuid
from sqlalchemy import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from src.models.account import Account, Member, Workspace

from .entity import AccountDBEntity, MemberDBEntity, WorkspaceDBEntity
from .exceptions import DBNotFoundError


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def _map_to_model(self, db_entity):
        raise NotImplementedError

    @abc.abstractmethod
    def _map_to_db_entity(self, entity):
        raise NotImplementedError

    def generate_id(self) -> str:
        uuid_object = uuid.uuid4()
        base32 = uuid_object.hex
        return base32

    def generate_slug(self) -> str:
        return shortuuid.uuid()


class AccountRepository(AbstractRepository):
    def __init__(self, connection: Connection):
        self.conn = connection

    def _map_to_db_entity(self, account: Account) -> AccountDBEntity:
        return AccountDBEntity(
            account_id=account.account_id,
            provider=account.provider,
            auth_user_id=account.auth_user_id,
            email=account.email,
            name=account.name,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    def _map_to_model(self, db_entity: AccountDBEntity) -> Account:
        return Account(
            account_id=db_entity.account_id,
            provider=db_entity.provider,
            auth_user_id=db_entity.auth_user_id,
            email=db_entity.email,
            name=db_entity.name,
            created_at=db_entity.created_at,
            updated_at=db_entity.updated_at,
        )

    async def _insert(self, item: AccountDBEntity):
        account_id = self.generate_id()
        query = """
            insert into account (
                account_id,
                provider,
                auth_user_id,
                email,
                name
            )
            values (
                :account_id,
                :provider,
                :auth_user_id,
                :email,
                :name
            )
            returning account_id, provider, auth_user_id, email, name, created_at, updated_at
        """
        parameters = {
            "account_id": account_id,
            "provider": item.provider,
            "auth_user_id": item.auth_user_id,
            "email": item.email,
            "name": item.name,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return AccountDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def _upsert(self, item: AccountDBEntity):
        query = """
            insert into account (
                account_id,
                provider,
                auth_user_id,
                email,
                name
            )
            values (
                :account_id,
                :provider,
                :auth_user_id,
                :email,
                :name
            )
            on conflict (account_id) do update set
                provider = :provider
                auth_user_id = :auth_user_id
                email = :email
                name = :name
                updated_at = now()
            returning account_id, provider, auth_user_id, email, name, created_at, updated_at
        """
        parameters = {
            "account_id": item.account_id,
            "provider": item.provider,
            "auth_user_id": item.auth_user_id,
            "email": item.email,
            "name": item.name,
        }
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return AccountDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def save(self, account: Account) -> Account:
        db_entity = self._map_to_db_entity(account)
        if db_entity.account_id is None:
            db_entity = await self._insert(db_entity)
        else:
            db_entity = await self._upsert(db_entity)
        return self._map_to_model(db_entity)

    async def find_by_auth_user_id(self, auth_user_id: str) -> Account | None:
        query = """
            select account_id, provider, auth_user_id, email, name, created_at, updated_at
            from account
            where auth_user_id = :auth_user_id
        """
        parameters = {"auth_user_id": auth_user_id}
        # async with self.db.begin() as conn:
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return self._map_to_model(AccountDBEntity(**result))

    async def get_by_auth_user_id(self, auth_user_id: str) -> Account:
        account = await self.find_by_auth_user_id(auth_user_id)
        if account is None:
            raise DBNotFoundError(f"Account with auth_user_id {auth_user_id} not found")
        return account


class WorkspaceRepository(AbstractRepository):
    def __init__(self, connection: Connection):
        self.conn = connection

    def _map_to_db_entity(self, workspace: Workspace) -> WorkspaceDBEntity:
        account = workspace.account
        if account is None:
            raise ValueError("Workspace must have an account")
        return WorkspaceDBEntity(
            workspace_id=workspace.workspace_id,
            account_id=account.account_id,
            name=workspace.name,
            slug=workspace.slug,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )

    def _map_to_model(
        self, db_entity: WorkspaceDBEntity, account: Account
    ) -> Workspace:
        if account is None:
            raise ValueError("Workspace must have an account")
        workspace = Workspace(
            workspace_id=db_entity.workspace_id,
            name=db_entity.name,
            created_at=db_entity.created_at,
            updated_at=db_entity.updated_at,
        )
        workspace.add_account(account)
        workspace.add_slug(db_entity.slug)
        return workspace

    async def _insert(self, item: WorkspaceDBEntity):
        workspace_id = self.generate_id()
        slug = self.generate_slug()
        query = """
            insert into workspace (
                workspace_id,
                account_id,
                name,
                slug
            )
            values (
                :workspace_id,
                :account_id,
                :name,
                :slug
            )
            returning workspace_id, account_id, name, slug, created_at, updated_at
        """
        parameters = {
            "workspace_id": workspace_id,
            "account_id": item.account_id,
            "name": item.name,
            "slug": slug,
        }
        # async with self.db.begin() as conn:
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return WorkspaceDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def _upsert(self, item: WorkspaceDBEntity):
        query = """
            insert into workspace (
                workspace_id,
                account_id,
                name,
                slug
            )
            values (
                :workspace_id,
                :account_id,
                :name,
                :slug
            )
            on conflict (workspace_id) do update set
                account_id = :account_id
                name = :name
                slug = :slug
                updated_at = now()
            returning workspace_id, account_id, name, slug, created_at, updated_at
        """
        parameters = {
            "workspace_id": item.workspace_id,
            "account_id": item.account_id,
            "name": item.name,
            "slug": item.slug,
        }
        # async with self.db.begin() as conn:
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return WorkspaceDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def save(self, workspace: Workspace) -> Workspace:
        if workspace.account is None:
            raise ValueError("Workspace must have an account")

        db_entity = self._map_to_db_entity(workspace)
        if db_entity.workspace_id is None:
            db_entity = await self._insert(db_entity)
        else:
            db_entity = await self._upsert(db_entity)
        return self._map_to_model(db_entity, workspace.account)

    async def find_all_by_account(self, account: Account) -> List[Workspace] | List:
        query = """
            select workspace_id, account_id, name, slug, created_at, updated_at
            from workspace
            where account_id = :account_id
            order by created_at desc
        """
        account_id = account.account_id
        parameters = {"account_id": account_id}
        # async with self.db.begin() as conn:
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        results = rows.mappings().all()
        return [
            self._map_to_model(WorkspaceDBEntity(**result), account)
            for result in results
        ]

    async def find_by_account_and_slug(
        self, account: Account, slug: str
    ) -> Workspace | None:
        query = """
            select workspace_id, account_id, name, slug, created_at, updated_at
            from workspace
            where account_id = :account_id
            and slug = :slug
        """
        account_id = account.account_id
        parameters = {"account_id": account_id, "slug": slug}
        # async with self.db.begin() as conn:
        rows = await self.conn.execute(statement=text(query), parameters=parameters)
        result = rows.mappings().first()
        if result is None:
            return None
        return self._map_to_model(WorkspaceDBEntity(**result), account)

    async def get_by_account_and_slug(self, account: Account, slug: str) -> Workspace:
        workspace = await self.find_by_account_and_slug(account, slug)
        if workspace is None:
            raise DBNotFoundError(f"Workspace with slug {slug} not found")
        return workspace


class MemberRepository(AbstractRepository):
    def __init__(self, connection: Connection):
        self.conn = connection

    def _map_to_db_entity(self, member: Member) -> MemberDBEntity:
        if member.workspace is None:
            raise ValueError("Member must have a workspace")
        if member.account is None:
            raise ValueError("Member must have an account")

        workspace_id = member.workspace.workspace_id
        account_id = member.account.account_id
        return MemberDBEntity(
            member_id=member.member_id,
            slug=member.slug,
            workspace_id=workspace_id,
            account_id=account_id,
            role=member.role.value,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )

    def _map_to_model(
        self,
        db_entity: MemberDBEntity,
        workspace: Workspace,
        account: Account,
    ) -> Member:
        return Member(
            workspace=workspace,
            account=account,
            member_id=db_entity.member_id,
            slug=db_entity.slug,
            role=db_entity.role,
            created_at=db_entity.created_at,
            updated_at=db_entity.updated_at,
        )

    async def _insert(self, item: MemberDBEntity):
        member_id = self.generate_id()
        slug = self.generate_slug()
        query = """
            insert into member (
                member_id,
                workspace_id,
                account_id,
                slug,
                role
            )
            values (
                :member_id,
                :workspace_id,
                :account_id,
                :slug,
                :role
            )
            returning member_id, workspace_id, account_id, slug, role, created_at, updated_at
        """
        parameters = {
            "member_id": member_id,
            "workspace_id": item.workspace_id,
            "account_id": item.account_id,
            "slug": slug,
            "role": item.role,
        }
        # async with self.db.begin() as conn:
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return MemberDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def _upsert(self, item: MemberDBEntity):
        query = """
            insert into member (
                member_id,
                workspace_id,
                account_id,
                slug,
                role
            )
            values (
                :member_id,
                :workspace_id,
                :account_id,
                :slug,
                :role
            )
            on conflict (member_id) do update set
                workspace_id = :workspace_id
                account_id = :account_id
                slug = :slug
                role = :role
                updated_at = now()
            returning member_id, workspace_id, account_id, slug, role, created_at, updated_at
        """
        parameters = {
            "member_id": item.member_id,
            "workspace_id": item.workspace_id,
            "account_id": item.account_id,
            "slug": item.slug,
            "role": item.role,
        }
        # async with self.db.begin() as conn:
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return MemberDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def save(self, member: Member) -> Member:
        if member.workspace is None:
            raise ValueError("Member must have a workspace")
        if member.account is None:
            raise ValueError("Member must have an account")

        db_entity = self._map_to_db_entity(member)
        if db_entity.member_id is None:
            db_entity = await self._insert(db_entity)
        else:
            db_entity = await self._upsert(db_entity)
        return self._map_to_model(db_entity, member.workspace, member.account)
