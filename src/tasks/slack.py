import asyncio
import logging
from typing import Dict

import sqlalchemy as db
from celery import chain

from src.config import engine, worker
from src.db.repository import SlackBotRepository, SlackWorkspaceRepository
from src.db.schema import SlackBotDB, SlackWorkspaceDB
from src.ext.slack import SlackWebAPIConnector
from src.models.account import Account, Workspace
from src.models.slack import SlackBot, SlackWorkspace

logger = logging.getLogger(__name__)


# We can also setup up pipeline for our provisioning Slack workspace tasks
# Reference:
#   https://blog.det.life/replacing-celery-tasks-inside-a-chain-b1328923fb02
#   https://docs.celeryq.dev/en/latest/userguide/canvas.html#chains
#


@worker.task(bind=True)
def authenticate(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run() -> dict:
        account = context["account"]
        workspace = context["workspace"]

        account = Account.from_dict(account)
        workspace = Workspace.from_dict(account, workspace)

        async with engine.begin() as connection:
            query = (
                db.select(
                    SlackWorkspaceDB.c.ref,
                    SlackWorkspaceDB.c.url,
                    SlackWorkspaceDB.c.name,
                    SlackWorkspaceDB.c.status,
                    SlackWorkspaceDB.c.created_at,
                    SlackWorkspaceDB.c.updated_at,
                    SlackBotDB.c.bot_id,
                    SlackBotDB.c.bot_user_ref,
                    SlackBotDB.c.bot_ref,
                    SlackBotDB.c.app_ref,
                    SlackBotDB.c.scope,
                    SlackBotDB.c.access_token,
                )
                .select_from(
                    db.join(
                        SlackWorkspaceDB,
                        SlackBotDB,
                        SlackWorkspaceDB.c.ref == SlackBotDB.c.slack_workspace_ref,
                    )
                )
                .where(SlackWorkspaceDB.c.workspace_id == workspace.workspace_id)
            )
            rows = await connection.execute(query)
            result = rows.mappings().first()

        slack_workspace = SlackWorkspace.from_dict(workspace, result)
        slack_bot = SlackBot.from_dict(slack_workspace, result)

        slack_api = SlackWebAPIConnector(access_token=slack_bot.access_token)
        response = slack_api.authenticate()

        slack_workspace.url = response.url
        slack_bot.bot_ref = response.bot_id

        async with engine.begin() as connection:
            repo = SlackWorkspaceRepository(connection)
            slack_workspace = await repo.upsert_by_workspace(slack_workspace)
            repo = SlackBotRepository(connection)
            slack_bot = await repo.upsert_by_workspace(slack_bot)

        logger.info(f"Provisioned Slack workspace: {slack_workspace}")
        logger.info(f"Provisioned Slack bot: {slack_bot}")

        result = {
            "workspace_id": workspace.workspace_id,
            "slack_workspace_ref": slack_workspace.ref,
            "slack_workspace_name": slack_workspace.name,
            "slack_workspace_status": slack_workspace.status,
            "bot_id": slack_bot.bot_id,
            "bot_user_ref": slack_bot.bot_user_ref,
            "bot_ref": slack_bot.bot_ref,
            "bot_access_token": slack_bot.access_token,
        }
        return result

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    return result


@worker.task(bind=True)
def set_status_ready(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run():
        ref = context["slack_workspace_ref"]
        query = (
            db.update(SlackWorkspaceDB)
            .where(SlackWorkspaceDB.c.ref == ref)
            .values(
                status=SlackWorkspace.status_ready(),
                updated_at=db.func.now(),
            )
        )
        async with engine.begin() as connection:
            await connection.execute(query)
        return True

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(run())
    logger.info(f"set_status_ready result: {result}")
    return context


@worker.task(bind=True)
def sync_status_syncing(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    logger.warning("TODO: implement this...")
    return context


@worker.task(bind=True)
def sync_channels(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    async def run() -> dict:
        bot_access_token = context["bot_access_token"]
        slack_api = SlackWebAPIConnector(access_token=bot_access_token)
        channels = slack_api.get_channels()
        print("************* result *************")
        for channel in channels:
            print(channel)
        return True

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    return context


@worker.task(bind=True)
def provision_pipeline(self, context: Dict):
    logger.info(f"{self.name} has parent with task id {self.request.parent_id}")
    logger.info(f"chain of {self.name}: {self.request.chain}")
    logger.info(f"self.request.id: {self.request.id}")

    return chain(
        authenticate.s(context),
        set_status_ready.s(),
        sync_status_syncing.s(),
        sync_channels.s(),
    ).apply_async()
