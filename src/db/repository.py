import abc
import uuid
from typing import List

import shortuuid
import sqlalchemy as db
from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from src.models.account import Account, Member, Workspace
from src.models.slack import SlackBot, SlackWorkspace

from .entity import AccountDBEntity, MemberDBEntity, WorkspaceDBEntity
from .exceptions import DBNotFoundError
from .schema import SlackBotDB, SlackWorkspaceDB, WorkspaceDB


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


class Repository:
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
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            if result is None:
                return None
            return self._map_to_model(AccountDBEntity(**result))
        except IntegrityError as e:
            raise e

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
            raise ValueError("Workspace must have an Account")
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
        if account is None or isinstance(account, Account) is False:
            raise ValueError("Workspace must have an Account")
        workspace = Workspace(
            account=account,
            workspace_id=db_entity.workspace_id,
            name=db_entity.name,
            slug=db_entity.slug,
            created_at=db_entity.created_at,
            updated_at=db_entity.updated_at,
        )
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

        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            return WorkspaceDBEntity(**result)
        except IntegrityError as e:
            raise e

    async def save(self, workspace: Workspace) -> Workspace:
        if workspace.account is None or isinstance(workspace.account, Account) is False:
            raise ValueError("Workspace must have an Account")

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

        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            results = rows.mappings().all()
            return [
                self._map_to_model(WorkspaceDBEntity(**result), account)
                for result in results
            ]
        except IntegrityError as e:
            raise e

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
        try:
            rows = await self.conn.execute(statement=text(query), parameters=parameters)
            result = rows.mappings().first()
            if result is None:
                return None
            return self._map_to_model(WorkspaceDBEntity(**result), account)
        except IntegrityError as e:
            raise e

    async def get_by_account_and_slug(self, account: Account, slug: str) -> Workspace:
        workspace = await self.find_by_account_and_slug(account, slug)
        if workspace is None:
            raise DBNotFoundError(f"Workspace with slug {slug} not found")
        return workspace

    async def find_by_workspace_id(self, workspace_id: str) -> Workspace | None:
        query = db.select(WorkspaceDB).where(WorkspaceDB.c.workspace_id == workspace_id)
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            if result is None:
                return None
            return Workspace(**result)
        except IntegrityError as e:
            raise e

    async def get_by_workspace_id(self, workspace_id: str) -> Workspace:
        workspace = await self.find_by_workspace_id(workspace_id)
        if workspace is None:
            raise DBNotFoundError(
                f"Workspace with workspace_id {workspace_id} not found"
            )
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


class SlackWorkspaceRepository(Repository):
    def __init__(self, connection: Connection):
        self.conn = connection

    async def save(self, slack_workspace: SlackWorkspace) -> SlackWorkspace:
        """
        Saves a SlackWorkspace if the SlackWorkspace already exists by ref (PK), update it.
        ref: is the PK and is the team id from Slack.
        """
        workspace = slack_workspace.workspace
        if workspace is None or isinstance(workspace, Workspace) is False:
            raise ValueError("SlackWorkspace must have associated Workspace")

        if slack_workspace.ref is None:
            raise ValueError("SlackWorkspace must have a ref - team id from Slack")

        query = (
            insert(SlackWorkspaceDB)
            .values(
                ref=slack_workspace.ref,
                workspace_id=workspace.workspace_id,
                url=slack_workspace.url,
                name=slack_workspace.name,
                status=slack_workspace.status,
                sync_status=slack_workspace.sync_status,
                synced_at=slack_workspace.synced_at,
            )
            .on_conflict_do_update(
                constraint="slack_workspace_ref_pkey",
                set_={
                    SlackWorkspaceDB.c.workspace_id: workspace.workspace_id,
                    SlackWorkspaceDB.c.url: slack_workspace.url,
                    SlackWorkspaceDB.c.name: slack_workspace.name,
                    SlackWorkspaceDB.c.status: slack_workspace.status,
                    SlackWorkspaceDB.c.sync_status: slack_workspace.sync_status,
                    SlackWorkspaceDB.c.synced_at: slack_workspace.synced_at,
                    SlackWorkspaceDB.c.updated_at: db.func.now(),
                },
            )
            .returning(
                SlackWorkspaceDB.c.ref,
                SlackWorkspaceDB.c.url,
                SlackWorkspaceDB.c.name,
                SlackWorkspaceDB.c.status,
                SlackWorkspaceDB.c.sync_status,
                SlackWorkspaceDB.c.synced_at,
            )
        )
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            return SlackWorkspace(
                workspace=workspace,
                **result,
            )
        except IntegrityError as e:
            raise e

    async def find_by_workspace(self, workspace: Workspace) -> SlackWorkspace | None:
        query = db.select(
            SlackWorkspaceDB.c.ref,
            SlackWorkspaceDB.c.url,
            SlackWorkspaceDB.c.name,
            SlackWorkspaceDB.c.status,
            SlackWorkspaceDB.c.sync_status,
            SlackWorkspaceDB.c.synced_at,
        ).where(SlackWorkspaceDB.c.workspace_id == workspace.workspace_id)
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            if result is None:
                return None
            return SlackWorkspace(workspace=workspace, **result)
        except IntegrityError as e:
            raise e

    async def upsert_by_workspace(
        self, slack_workspace: SlackWorkspace
    ) -> SlackWorkspace:
        workspace = slack_workspace.workspace
        if workspace is None or isinstance(workspace, Workspace) is False:
            raise ValueError("SlackWorkspace must have associated Workspace")

        if slack_workspace.ref is None:
            raise ValueError("SlackWorkspace must have a ref - team id from Slack")

        query = (
            insert(SlackWorkspaceDB)
            .values(
                workspace_id=workspace.workspace_id,
                ref=slack_workspace.ref,
                url=slack_workspace.url,
                name=slack_workspace.name,
                status=slack_workspace.status,
                sync_status=slack_workspace.sync_status,
                synced_at=slack_workspace.synced_at,
            )
            .on_conflict_do_update(
                constraint="slack_workspace_workspace_id_key",
                set_={
                    SlackWorkspaceDB.c.ref: slack_workspace.ref,
                    SlackWorkspaceDB.c.url: slack_workspace.url,
                    SlackWorkspaceDB.c.name: slack_workspace.name,
                    SlackWorkspaceDB.c.status: slack_workspace.status,
                    SlackWorkspaceDB.c.sync_status: slack_workspace.sync_status,
                    SlackWorkspaceDB.c.synced_at: slack_workspace.synced_at,
                    SlackWorkspaceDB.c.updated_at: db.func.now(),
                },
            )
            .returning(
                SlackWorkspaceDB.c.ref,
                SlackWorkspaceDB.c.url,
                SlackWorkspaceDB.c.name,
                SlackWorkspaceDB.c.status,
                SlackWorkspaceDB.c.sync_status,
                SlackWorkspaceDB.c.synced_at,
            )
        )
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            return SlackWorkspace(
                workspace=workspace,
                **result,
            )
        except IntegrityError as e:
            raise e


class SlackBotRepository(Repository):
    def __init__(self, connection: Connection):
        self.conn = connection

    async def save(self, slack_bot: SlackBot) -> SlackBot:
        """
        Save a SlackBot to the database. If the SlackBot already exists by bot_id, update it.
        bot_id: the PK.
        """
        slack_workspace = slack_bot.slack_workspace
        bot_id = slack_bot.bot_id
        if (
            slack_workspace is None
            or isinstance(slack_workspace, SlackWorkspace) is False
        ):
            raise ValueError("SlackBot must have associated SlackWorkspace")

        if slack_bot.bot_user_ref is None:
            raise ValueError(
                "SlackBot must have a bot_user_id referenced as bot_user_ref from Slack"
            )

        if bot_id is None:
            bot_id = self.generate_id()

        query = (
            insert(SlackBotDB)
            .values(
                bot_id=bot_id,
                slack_workspace_ref=slack_workspace.ref,
                bot_user_ref=slack_bot.bot_user_ref,
                bot_ref=slack_bot.bot_ref,
                app_ref=slack_bot.app_ref,
                scope=slack_bot.scope,
                access_token=slack_bot.access_token,
            )
            .on_conflict_do_update(
                constraint="slack_bot_bot_id_pkey",
                set_={
                    SlackBotDB.c.slack_workspace_ref: slack_workspace.ref,
                    SlackBotDB.c.bot_user_ref: slack_bot.bot_user_ref,
                    SlackBotDB.c.bot_ref: slack_bot.bot_ref,
                    SlackBotDB.c.app_ref: slack_bot.app_ref,
                    SlackBotDB.c.scope: slack_bot.scope,
                    SlackBotDB.c.access_token: slack_bot.access_token,
                },
            )
            .returning(
                SlackBotDB.c.bot_id,
                SlackBotDB.c.bot_user_ref,
                SlackBotDB.c.bot_ref,
                SlackBotDB.c.app_ref,
                SlackBotDB.c.scope,
                SlackBotDB.c.access_token,
            )
        )
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            return SlackBot(
                slack_workspace=slack_workspace,
                **result,
            )
        except IntegrityError as e:
            raise e

    async def upsert_by_workspace(self, slack_bot: SlackBot) -> SlackBot:
        slack_workspace = slack_bot.slack_workspace
        bot_id = slack_bot.bot_id
        if (
            slack_workspace is None
            or isinstance(slack_workspace, SlackWorkspace) is False
        ):
            raise ValueError("SlackBot must have associated SlackWorkspace")

        if slack_bot.bot_user_ref is None:
            raise ValueError("SlackBot must have a bot_user_ref from Slack")

        if bot_id is None:
            bot_id = self.generate_id()

        query = (
            insert(SlackBotDB)
            .values(
                slack_workspace_ref=slack_workspace.ref,
                bot_id=bot_id,
                bot_user_ref=slack_bot.bot_user_ref,
                bot_ref=slack_bot.bot_ref,
                app_ref=slack_bot.app_ref,
                scope=slack_bot.scope,
                access_token=slack_bot.access_token,
            )
            .on_conflict_do_update(
                constraint="slack_bot_slack_workspace_ref_key",
                set_={
                    SlackBotDB.c.bot_id: bot_id,
                    SlackBotDB.c.bot_user_ref: slack_bot.bot_user_ref,
                    SlackBotDB.c.bot_ref: slack_bot.bot_ref,
                    SlackBotDB.c.app_ref: slack_bot.app_ref,
                    SlackBotDB.c.scope: slack_bot.scope,
                    SlackBotDB.c.access_token: slack_bot.access_token,
                },
            )
            .returning(
                SlackBotDB.c.bot_id,
                SlackBotDB.c.bot_user_ref,
                SlackBotDB.c.bot_ref,
                SlackBotDB.c.app_ref,
                SlackBotDB.c.scope,
                SlackBotDB.c.access_token,
            )
        )
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            return SlackBot(
                slack_workspace=slack_workspace,
                **result,
            )
        except IntegrityError as e:
            raise e

    async def find_by_workspace(
        self, slack_workspace: SlackWorkspace
    ) -> SlackBot | None:
        query = db.select(
            SlackBotDB.c.bot_id,
            SlackBotDB.c.bot_user_ref,
            SlackBotDB.c.bot_ref,
            SlackBotDB.c.app_ref,
            SlackBotDB.c.scope,
            SlackBotDB.c.access_token,
        ).where(SlackBotDB.c.slack_workspace_ref == slack_workspace.ref)
        try:
            rows = await self.conn.execute(query)
            result = rows.mappings().first()
            if result is None:
                return None
            return SlackBot(slack_workspace=slack_workspace, **result)
        except IntegrityError as e:
            raise e
